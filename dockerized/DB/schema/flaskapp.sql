--Author: skondla@me.com
--Purpose: Create schema for db restore web App.

drop table if EXISTS public.user;
drop table if EXISTS public.userinfo;
drop sequence if EXISTS public.userinfo_id_seq ;
drop sequence if EXISTS public.user_id_seq;

DROP USER skondla;

DROP DATABASE IF EXISTS flaskapp ;

CREATE DATABASE flaskapp;

--SET SKONDLA_PG_PASS TO current_setting('SKONDLA_PG_PASS');

CREATE USER skondla with password :SKONDLA_PG_PASS;

ALTER DATABASE flaskapp OWNER TO skondla;

\connect flaskapp 

CREATE SEQUENCE public.user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_id_seq OWNER TO skondla;

CREATE TABLE public."user" (
    id integer DEFAULT nextval('public.user_id_seq'::regclass) NOT NULL,
    email character varying(100),
    password character varying(1000),
    name character varying(50)
);


ALTER TABLE public."user" OWNER TO skondla;

CREATE SEQUENCE public.userinfo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.userinfo_id_seq OWNER TO skondla;


CREATE TABLE public.userinfo (
    id integer DEFAULT nextval('public.userinfo_id_seq'::regclass) NOT NULL,
    email character varying(100),
    ip character varying(50),
    "time" character varying(60),
    requesttype character varying(30),
    endpoint character varying(300),
    comments character varying(200)
);


ALTER TABLE public.userinfo OWNER TO skondla;
ALTER TABLE public.user OWNER TO skondla;
--ALTER SEQUENCE public.user_id_seq TO skondla;
--ALTER SEQUENCE public.userinfo_id_seq TO skondla;


SELECT pg_catalog.setval('public.user_id_seq', 33, true);
SELECT pg_catalog.setval('public.userinfo_id_seq', 37, true);

/*
REVOKE ALL ON SCHEMA public FROM rdsadmin;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO dbadmin;
GRANT ALL ON SCHEMA public TO PUBLIC;
*/