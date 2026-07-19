#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: Multi-step agent orchestrator for the DB restore workflow, built on
#          LangGraph's ReAct agent (LangChain tools + Claude). Plans and
#          sequences the existing atomic RDS operations (restore -> status
#          check -> optional attach -> notify) that previously required three
#          separate manual form submissions.
# -*- coding: utf-8 -*-

import os
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from botocore.exceptions import ClientError
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent

import rds_ops

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
MAX_TOOL_STEPS = 8
MAX_WAIT_SECONDS_PER_CALL = 15
MAX_TOTAL_WAIT_SECONDS = 30
RECURSION_LIMIT = 50

SYSTEM_PROMPT = """\
You are the workflow orchestrator for an RDS DB Restore Management Tool.
You have tools to restore a snapshot, check status, attach an instance to a
cluster, and send a team notification. Given the operator's request, plan and
execute the minimum necessary tool calls, in this order:

1. Always call restore_snapshot first.
2. Call check_db_status once immediately after the restore (wait_seconds=0).
   You may call it a second time with a short wait_seconds (<=15) if useful,
   but never more than twice total.
3. Only call attach_instance if the operator explicitly asked to attach an
   instance AND the endpoint is an Aurora cluster (contains "cluster"). Skip
   it otherwise and say why.
4. Call notify once after the restore, and once more after an attach if one
   was performed.

Do not call any tool more than twice. If a tool call fails, do not retry it
more than once, and explain the failure in your final summary instead of
attempting further destructive actions. When you are done, reply with a
short plain-text summary for the operator: what was done, the resulting
endpoint(s), and the final observed status.
"""


@dataclass
class OrchestrationStep:
    tool: str
    input: dict
    result: str
    ok: bool


@dataclass
class OrchestrationResult:
    final_message: str
    steps: list = field(default_factory=list)


class RestoreOrchestrator:
    """Plans and executes the restore -> status -> attach -> notify workflow
    using a LangGraph ReAct agent over LangChain tools wrapping the existing
    RDS operations in rds_ops.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured.")
        self._chat_model = ChatAnthropic(model=model, api_key=api_key, temperature=0)

    def _build_tools(
        self,
        steps: list,
        wait_budget: dict,
        on_step: Optional[Callable[[str, str, str], None]],
    ) -> list:
        def _record(name: str, tool_input: dict, result_text: str, ok: bool) -> str:
            steps.append(OrchestrationStep(tool=name, input=tool_input, result=result_text, ok=ok))
            if on_step:
                on_step(name, str(tool_input), result_text)
            return result_text

        def restore_snapshot(snapshot_name: str, source_endpoint: str) -> str:
            """Restore an RDS DB instance or cluster from a snapshot. Looks up
            subnet/security-group/engine info from the source endpoint and
            kicks off the restore. Returns the new endpoint identifier.
            Endpoints containing 'cluster' are treated as Aurora clusters.
            """
            snapshot_name = snapshot_name.strip()
            source_endpoint = source_endpoint.strip()
            tool_input = {"snapshot_name": snapshot_name, "source_endpoint": source_endpoint}
            try:
                new_endpoint = snapshot_name + "." + source_endpoint.split(".", 1)[1]
                rds_ops.db_restore(snapshot_name, source_endpoint)
                return _record(
                    "restore_snapshot", tool_input,
                    f"Restore initiated. New endpoint: {new_endpoint}", True,
                )
            except ClientError as exc:
                return _record(
                    "restore_snapshot", tool_input, f"Error: AWS call failed: {exc}", False
                )

        def check_db_status(source_endpoint: str, new_endpoint: str, wait_seconds: int = 0) -> str:
            """Check the current status of a restored DB instance or cluster.
            Optionally wait a few seconds first (0-15) to let AWS state settle.
            """
            tool_input = {
                "source_endpoint": source_endpoint,
                "new_endpoint": new_endpoint,
                "wait_seconds": wait_seconds,
            }
            try:
                wait = min(int(wait_seconds or 0), MAX_WAIT_SECONDS_PER_CALL)
                wait = min(wait, max(0, MAX_TOTAL_WAIT_SECONDS - wait_budget["used"]))
                if wait > 0:
                    time.sleep(wait)
                    wait_budget["used"] += wait
                state = rds_ops.db_status(source_endpoint, new_endpoint)
                return _record("check_db_status", tool_input, f"Status: {state}", True)
            except ClientError as exc:
                return _record(
                    "check_db_status", tool_input, f"Error: AWS call failed: {exc}", False
                )

        def attach_instance(cluster_endpoint: str, instance_class: str) -> str:
            """Attach a new reader instance to an existing Aurora cluster.
            Only valid when the endpoint is a cluster.
            """
            cluster_endpoint = cluster_endpoint.strip()
            instance_class = instance_class.strip()
            tool_input = {"cluster_endpoint": cluster_endpoint, "instance_class": instance_class}
            if "cluster" not in cluster_endpoint:
                return _record(
                    "attach_instance", tool_input,
                    f"Error: {cluster_endpoint} is not a cluster; cannot attach.", False,
                )
            try:
                instance_name = rds_ops.db_attach(cluster_endpoint, instance_class)
                new_endpoint = f"{instance_name}.{cluster_endpoint.split('.', 1)[1]}"
                return _record(
                    "attach_instance", tool_input,
                    f"Attach initiated. Instance: {instance_name}, new endpoint: {new_endpoint}",
                    True,
                )
            except ClientError as exc:
                return _record(
                    "attach_instance", tool_input, f"Error: AWS call failed: {exc}", False
                )

        def notify(identifier: str, endpoint: str, state: str, action: str) -> str:
            """Send a Slack message and email notifying the team of a workflow
            state change. Call once after restore, and once more after an
            attach if one was performed.
            """
            tool_input = {"identifier": identifier, "endpoint": endpoint, "state": state, "action": action}
            rds_ops.slack_post(identifier, endpoint, state, action, "dbAgentOrchestrator")
            rds_ops.send_email(identifier, endpoint, state)
            return _record("notify", tool_input, "Notification sent.", True)

        return [
            StructuredTool.from_function(func=restore_snapshot, name="restore_snapshot"),
            StructuredTool.from_function(func=check_db_status, name="check_db_status"),
            StructuredTool.from_function(func=attach_instance, name="attach_instance"),
            StructuredTool.from_function(func=notify, name="notify"),
        ]

    def run(
        self,
        goal: str,
        snapshot_name: str,
        source_endpoint: str,
        target_instance_class: Optional[str] = None,
        on_step: Optional[Callable[[str, str, str], None]] = None,
    ) -> OrchestrationResult:
        steps: list[OrchestrationStep] = []
        wait_budget = {"used": 0}
        tools = self._build_tools(steps, wait_budget, on_step)
        agent = create_react_agent(self._chat_model, tools, prompt=SYSTEM_PROMPT)

        user_prompt = (
            f"Operator request: {goal}\n"
            f"snapshot_name: {snapshot_name}\n"
            f"source_endpoint: {source_endpoint}\n"
            f"target_instance_class: {target_instance_class or '(not requested)'}"
        )

        final_message = "Stopped after reaching the maximum number of workflow steps."
        tool_call_count = 0
        for update in agent.stream(
            {"messages": [("user", user_prompt)]},
            config={"recursion_limit": RECURSION_LIMIT},
            stream_mode="updates",
        ):
            for node_update in update.values():
                for msg in node_update.get("messages", []):
                    if not isinstance(msg, AIMessage):
                        continue
                    if msg.tool_calls:
                        tool_call_count += len(msg.tool_calls)
                    elif isinstance(msg.content, str) and msg.content:
                        final_message = msg.content
            if tool_call_count >= MAX_TOOL_STEPS:
                break

        return OrchestrationResult(final_message=final_message, steps=steps)
