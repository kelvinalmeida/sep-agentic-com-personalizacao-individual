--
-- PostgreSQL database dump
--

\restrict YpXc8SBng0Nw0633y5MdcFKa1gklBjN9rdDon5bJxsS1qGYyN42Sn2DUXcuzQrY

-- Dumped from database version 18.3 (Debian 18.3-1.pgdg13+1)
-- Dumped by pg_dump version 18.3 (Debian 18.3-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: general_message; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.general_message (
    id integer NOT NULL,
    username character varying(100) NOT NULL,
    content text NOT NULL,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    message_id integer NOT NULL
);


ALTER TABLE public.general_message OWNER TO "user";

--
-- Name: general_message_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.general_message_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.general_message_id_seq OWNER TO "user";

--
-- Name: general_message_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.general_message_id_seq OWNED BY public.general_message.id;


--
-- Name: message; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.message (
    id integer NOT NULL
);


ALTER TABLE public.message OWNER TO "user";

--
-- Name: message_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.message_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.message_id_seq OWNER TO "user";

--
-- Name: message_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.message_id_seq OWNED BY public.message.id;


--
-- Name: private_message; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.private_message (
    id integer NOT NULL,
    sender_id integer NOT NULL,
    username character varying(80) NOT NULL,
    target_username character varying(80) NOT NULL,
    content text NOT NULL,
    "timestamp" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    message_id integer NOT NULL
);


ALTER TABLE public.private_message OWNER TO "user";

--
-- Name: private_message_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.private_message_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.private_message_id_seq OWNER TO "user";

--
-- Name: private_message_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.private_message_id_seq OWNED BY public.private_message.id;


--
-- Name: strategies; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.strategies (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    score integer DEFAULT 0
);


ALTER TABLE public.strategies OWNER TO "user";

--
-- Name: strategies_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.strategies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.strategies_id_seq OWNER TO "user";

--
-- Name: strategies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.strategies_id_seq OWNED BY public.strategies.id;


--
-- Name: tactics; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.tactics (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    "time" double precision,
    chat_id integer,
    strategy_id integer NOT NULL
);


ALTER TABLE public.tactics OWNER TO "user";

--
-- Name: tactics_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.tactics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tactics_id_seq OWNER TO "user";

--
-- Name: tactics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.tactics_id_seq OWNED BY public.tactics.id;


--
-- Name: general_message id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.general_message ALTER COLUMN id SET DEFAULT nextval('public.general_message_id_seq'::regclass);


--
-- Name: message id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.message ALTER COLUMN id SET DEFAULT nextval('public.message_id_seq'::regclass);


--
-- Name: private_message id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.private_message ALTER COLUMN id SET DEFAULT nextval('public.private_message_id_seq'::regclass);


--
-- Name: strategies id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.strategies ALTER COLUMN id SET DEFAULT nextval('public.strategies_id_seq'::regclass);


--
-- Name: tactics id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.tactics ALTER COLUMN id SET DEFAULT nextval('public.tactics_id_seq'::regclass);


--
-- Data for Name: general_message; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.general_message (id, username, content, "timestamp", message_id) FROM stdin;
1	kelvin123	aviso - kelvin123 entrou na sala geral.	2025-12-06 00:50:05.133227	2
2	kelvin123	aviso - kelvin123 entrou na sala geral.	2025-12-06 00:51:04.762456	2
3	kelvin123	aviso - kelvin123 entrou na sala geral.	2025-12-06 00:59:27.285803	2
4	ana	Oi	2026-04-19 02:02:37.817107	2
5	joao	oi	2026-04-19 02:02:47.122614	2
6	kelvin123	oi	2026-04-19 02:03:13.700763	2
7	kelvin123	oi	2026-04-19 02:05:17.614329	2
8	ana	Oi chato kkkk	2026-04-19 02:05:42.748202	2
9	kelvin123	ana buche	2026-04-19 02:05:50.607642	2
10	ana	Oi	2026-04-20 13:12:29.61921	2
11	ana	Vamos estudar	2026-04-20 13:12:36.627017	2
12	ana	Ggg	2026-04-20 13:21:43.581007	2
13	kelvin	kk	2026-04-20 13:21:50.330032	2
14	fabricio	gg	2026-04-20 13:21:54.102533	2
15	maria	ss	2026-04-20 13:21:57.484592	2
16	joao	aaa	2026-04-20 13:22:00.73536	2
17	ana	Ffg	2026-04-20 13:22:11.98727	2
18	maria	sss	2026-04-20 13:22:14.376257	2
\.


--
-- Data for Name: message; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.message (id) FROM stdin;
1
2
3
4
5
6
\.


--
-- Data for Name: private_message; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.private_message (id, sender_id, username, target_username, content, "timestamp", message_id) FROM stdin;
1	1	kelvin123	ana	oi	2026-04-19 02:02:58.332397+00	2
2	1	kelvin123	ana	oi	2026-04-20 13:12:49.41233+00	2
\.


--
-- Data for Name: strategies; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.strategies (id, name, score) FROM stdin;
1	estra 1	8
2	estra 2	7
3	strategia mudandanca de estrategia	9
4	aprender python	9
5	python	9
6	Ruby	10
8	Aula 01 - Microservices no nível Básico	8
9	Aula 02 - Microservices no nível Intermediário	8
\.


--
-- Data for Name: tactics; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.tactics (id, name, description, "time", chat_id, strategy_id) FROM stdin;
1	Reuso	2	2	\N	1
2	Debate Sincrono	2	2	1	1
3	Apresentacao Sincrona	https://meet.google.com/dxt-mbyg-gvs	2	\N	1
4	Envio de Informacao	2	2	\N	1
5	Debate Sincrono	3	3	2	2
6	Apresentacao Sincrona	https://meet.google.com/dxt-mbyg-gvs	3	\N	2
7	Envio de Informacao	3	3	\N	2
8	Reuso	3	3	\N	2
9	Debate Sincrono	\N	0.1	3	3
10	Mudanca de Estrategia	1	1	\N	3
11	Reuso	Ler apostila	0.2	\N	4
12	Debate Sincrono	debater o que foi aprendido	0.2	4	4
13	Envio de Informacao	enviando material por email	0.2	\N	4
14	Reuso	Veja os vídeos	0.2	\N	5
15	Debate Sincrono	vamos debater	0.2	5	5
16	Mudanca de Estrategia	4	0.2	\N	5
17	Reuso	3	0.2	\N	6
18	Debate Sincrono	vamos debater	0.2	5	6
19	Regra	3	0.2	\N	6
22	Reuso	Leiam os dois PDF's sobre microserviços.	60	\N	8
23	Apresentacao Sincrona	https://meet.google.com/izy-cnxj-jzo	60	\N	8
24	Reuso	Leiam o PDF	30	\N	9
25	Debate Sincrono	Debater o que aprendemos	30	6	9
26	Apresentacao Sincrona	https://meet.google.com/pxb-pzyw-apc	30	\N	9
\.


--
-- Name: general_message_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.general_message_id_seq', 18, true);


--
-- Name: message_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.message_id_seq', 6, true);


--
-- Name: private_message_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.private_message_id_seq', 2, true);


--
-- Name: strategies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.strategies_id_seq', 9, true);


--
-- Name: tactics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.tactics_id_seq', 26, true);


--
-- Name: general_message general_message_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.general_message
    ADD CONSTRAINT general_message_pkey PRIMARY KEY (id);


--
-- Name: message message_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.message
    ADD CONSTRAINT message_pkey PRIMARY KEY (id);


--
-- Name: private_message private_message_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.private_message
    ADD CONSTRAINT private_message_pkey PRIMARY KEY (id);


--
-- Name: strategies strategies_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.strategies
    ADD CONSTRAINT strategies_pkey PRIMARY KEY (id);


--
-- Name: tactics tactics_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.tactics
    ADD CONSTRAINT tactics_pkey PRIMARY KEY (id);


--
-- Name: private_message fk_message_parent; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.private_message
    ADD CONSTRAINT fk_message_parent FOREIGN KEY (message_id) REFERENCES public.message(id) ON DELETE CASCADE;


--
-- Name: general_message fk_message_room; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.general_message
    ADD CONSTRAINT fk_message_room FOREIGN KEY (message_id) REFERENCES public.message(id) ON DELETE CASCADE;


--
-- Name: tactics fk_strategies; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.tactics
    ADD CONSTRAINT fk_strategies FOREIGN KEY (strategy_id) REFERENCES public.strategies(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict YpXc8SBng0Nw0633y5MdcFKa1gklBjN9rdDon5bJxsS1qGYyN42Sn2DUXcuzQrY

