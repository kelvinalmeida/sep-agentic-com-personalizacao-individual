--
-- PostgreSQL database dump
--

\restrict Z3uIOQm9WpdPr3O6ePZBjQsdzeUx0xTakmYCHgEKjdEn9ygcREkQeUOH6G9n0AS

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
-- Name: extra_notes; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.extra_notes (
    id integer NOT NULL,
    estudante_username character varying(100) NOT NULL,
    student_id integer NOT NULL,
    extra_notes double precision DEFAULT 0.0 NOT NULL,
    session_id integer NOT NULL
);


ALTER TABLE public.extra_notes OWNER TO "user";

--
-- Name: extra_notes_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.extra_notes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.extra_notes_id_seq OWNER TO "user";

--
-- Name: extra_notes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.extra_notes_id_seq OWNED BY public.extra_notes.id;


--
-- Name: session; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.session (
    id integer NOT NULL,
    status character varying(50) NOT NULL,
    code character varying(50) NOT NULL,
    start_time timestamp without time zone,
    current_tactic_index integer DEFAULT 0,
    current_tactic_started_at timestamp without time zone,
    original_strategy_id character varying(50),
    use_agent boolean DEFAULT false,
    rating_average double precision DEFAULT 0.0,
    rating_count integer DEFAULT 0,
    executed_indices text DEFAULT '[]'::text,
    end_on_next_completion boolean DEFAULT false
);


ALTER TABLE public.session OWNER TO "user";

--
-- Name: session_domains; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.session_domains (
    session_id integer NOT NULL,
    domain_id character varying(50) NOT NULL
);


ALTER TABLE public.session_domains OWNER TO "user";

--
-- Name: session_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.session_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.session_id_seq OWNER TO "user";

--
-- Name: session_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.session_id_seq OWNED BY public.session.id;


--
-- Name: session_ratings; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.session_ratings (
    id integer NOT NULL,
    session_id integer NOT NULL,
    student_id character varying(50) NOT NULL,
    rating integer NOT NULL
);


ALTER TABLE public.session_ratings OWNER TO "user";

--
-- Name: session_ratings_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.session_ratings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.session_ratings_id_seq OWNER TO "user";

--
-- Name: session_ratings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.session_ratings_id_seq OWNED BY public.session_ratings.id;


--
-- Name: session_strategies; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.session_strategies (
    session_id integer NOT NULL,
    strategy_id character varying(50) NOT NULL
);


ALTER TABLE public.session_strategies OWNER TO "user";

--
-- Name: session_students; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.session_students (
    session_id integer NOT NULL,
    student_id character varying(50) NOT NULL
);


ALTER TABLE public.session_students OWNER TO "user";

--
-- Name: session_teachers; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.session_teachers (
    session_id integer NOT NULL,
    teacher_id character varying(50) NOT NULL
);


ALTER TABLE public.session_teachers OWNER TO "user";

--
-- Name: verified_answers; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.verified_answers (
    id integer NOT NULL,
    student_name character varying(100) NOT NULL,
    student_id character varying(50) NOT NULL,
    answers jsonb NOT NULL,
    score integer DEFAULT 0 NOT NULL,
    session_id integer NOT NULL
);


ALTER TABLE public.verified_answers OWNER TO "user";

--
-- Name: verified_answers_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.verified_answers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.verified_answers_id_seq OWNER TO "user";

--
-- Name: verified_answers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.verified_answers_id_seq OWNED BY public.verified_answers.id;


--
-- Name: extra_notes id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.extra_notes ALTER COLUMN id SET DEFAULT nextval('public.extra_notes_id_seq'::regclass);


--
-- Name: session id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session ALTER COLUMN id SET DEFAULT nextval('public.session_id_seq'::regclass);


--
-- Name: session_ratings id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session_ratings ALTER COLUMN id SET DEFAULT nextval('public.session_ratings_id_seq'::regclass);


--
-- Name: verified_answers id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.verified_answers ALTER COLUMN id SET DEFAULT nextval('public.verified_answers_id_seq'::regclass);


--
-- Data for Name: extra_notes; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.extra_notes (id, estudante_username, student_id, extra_notes, session_id) FROM stdin;
1	aluno_demo	1	9.5	2
\.


--
-- Data for Name: session; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.session (id, status, code, start_time, current_tactic_index, current_tactic_started_at, original_strategy_id, use_agent, rating_average, rating_count, executed_indices, end_on_next_completion) FROM stdin;
2	finished	LIVE5678	2026-04-19 00:31:17.576849	2	2026-04-19 01:52:39.200807	\N	f	0	0	[1]	f
15	finished	1FOVOO97	2026-04-27 11:21:22.134683	2	2026-04-27 12:42:31.949811	\N	t	5	7	[0, 1]	f
1	finished	CODE1234	2026-04-20 17:46:50.921421	0	2026-04-20 17:46:50.921421	\N	t	0	0	[]	f
14	finished	Q578N9YF	2026-04-22 10:55:24.357368	1	2026-04-22 19:25:35.973599	\N	t	4.833333333333333	6	[0]	f
\.


--
-- Data for Name: session_domains; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.session_domains (session_id, domain_id) FROM stdin;
1	1
2	1
14	21
15	24
\.


--
-- Data for Name: session_ratings; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.session_ratings (id, session_id, student_id, rating) FROM stdin;
1	14	11	5
2	14	23	5
8	14	16	5
9	14	13	5
10	14	20	4
11	14	28	5
12	15	28	5
13	15	42	5
14	15	34	5
15	15	11	5
16	15	10	5
17	15	44	5
18	15	41	5
\.


--
-- Data for Name: session_strategies; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.session_strategies (session_id, strategy_id) FROM stdin;
1	1
2	3
14	8
15	9
\.


--
-- Data for Name: session_students; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.session_students (session_id, student_id) FROM stdin;
1	1
2	1
2	9
14	10
14	11
14	12
14	13
14	14
14	15
14	18
14	19
14	16
14	17
14	20
14	21
14	22
14	23
14	24
14	26
14	27
14	28
1	6
15	7
15	18
15	15
15	11
15	14
15	22
15	21
15	29
15	16
15	30
15	32
14	33
15	34
15	31
15	17
15	28
15	20
15	36
15	37
15	38
15	10
15	39
15	33
15	42
15	41
15	44
15	13
14	30
14	39
\.


--
-- Data for Name: session_teachers; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.session_teachers (session_id, teacher_id) FROM stdin;
1	1
2	1
14	2
15	2
15	3
\.


--
-- Data for Name: verified_answers; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.verified_answers (id, student_name, student_id, answers, score, session_id) FROM stdin;
1	aluno_demo	1	[{"answer": 2, "correct": true, "exercise_id": 101}, {"answer": 0, "correct": false, "exercise_id": 102}]	50	2
2	lucas	7	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
3	GuiCoutinho	30	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 1, "correct": false, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	4	15
4	Jesm	28	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
5	caiomascarenhas	32	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
6	LarissaFDS	21	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
7	Vitor	34	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
8	riane_santos	37	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
9	gabo2301	14	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
10	katochi	11	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
11	Otavio	22	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
12	JhonathanMilk	16	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
13	plaercio1812	15	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 3, "correct": false, "exercise_id": 13}]	4	15
14	arthur.alves	29	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
15	marcosdouglas	42	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
16	FernandoEBR	10	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
17	alisonbms	18	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
18	Henriiqu_ee	38	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
19	Marrcela	33	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
20	Tatiane	31	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
21	Marcelo Eduardo	44	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
22	David Kelve Oliveira Barbosa	20	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
23	PedroNeves34	17	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
24	otavio	13	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
25	Fsmota12	41	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
26	Lucas_Portugues	39	[{"answer": 2, "correct": true, "exercise_id": 9}, {"answer": 2, "correct": true, "exercise_id": 10}, {"answer": 1, "correct": true, "exercise_id": 11}, {"answer": 3, "correct": true, "exercise_id": 12}, {"answer": 2, "correct": true, "exercise_id": 13}]	5	15
\.


--
-- Name: extra_notes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.extra_notes_id_seq', 2, true);


--
-- Name: session_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.session_id_seq', 15, true);


--
-- Name: session_ratings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.session_ratings_id_seq', 18, true);


--
-- Name: verified_answers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.verified_answers_id_seq', 26, true);


--
-- Name: extra_notes extra_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.extra_notes
    ADD CONSTRAINT extra_notes_pkey PRIMARY KEY (id);


--
-- Name: session session_code_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_code_key UNIQUE (code);


--
-- Name: session_domains session_domains_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session_domains
    ADD CONSTRAINT session_domains_pkey PRIMARY KEY (session_id, domain_id);


--
-- Name: session session_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_pkey PRIMARY KEY (id);


--
-- Name: session_ratings session_ratings_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session_ratings
    ADD CONSTRAINT session_ratings_pkey PRIMARY KEY (id);


--
-- Name: session_ratings session_ratings_session_id_student_id_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session_ratings
    ADD CONSTRAINT session_ratings_session_id_student_id_key UNIQUE (session_id, student_id);


--
-- Name: session_strategies session_strategies_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session_strategies
    ADD CONSTRAINT session_strategies_pkey PRIMARY KEY (session_id, strategy_id);


--
-- Name: session_students session_students_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session_students
    ADD CONSTRAINT session_students_pkey PRIMARY KEY (session_id, student_id);


--
-- Name: session_teachers session_teachers_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session_teachers
    ADD CONSTRAINT session_teachers_pkey PRIMARY KEY (session_id, teacher_id);


--
-- Name: verified_answers verified_answers_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.verified_answers
    ADD CONSTRAINT verified_answers_pkey PRIMARY KEY (id);


--
-- Name: session_ratings fk_rating_session; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session_ratings
    ADD CONSTRAINT fk_rating_session FOREIGN KEY (session_id) REFERENCES public.session(id) ON DELETE CASCADE;


--
-- Name: session_domains fk_session_domains; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session_domains
    ADD CONSTRAINT fk_session_domains FOREIGN KEY (session_id) REFERENCES public.session(id) ON DELETE CASCADE;


--
-- Name: extra_notes fk_session_extra_notes; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.extra_notes
    ADD CONSTRAINT fk_session_extra_notes FOREIGN KEY (session_id) REFERENCES public.session(id) ON DELETE CASCADE;


--
-- Name: session_strategies fk_session_strategies; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session_strategies
    ADD CONSTRAINT fk_session_strategies FOREIGN KEY (session_id) REFERENCES public.session(id) ON DELETE CASCADE;


--
-- Name: session_students fk_session_students; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session_students
    ADD CONSTRAINT fk_session_students FOREIGN KEY (session_id) REFERENCES public.session(id) ON DELETE CASCADE;


--
-- Name: session_teachers fk_session_teachers; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.session_teachers
    ADD CONSTRAINT fk_session_teachers FOREIGN KEY (session_id) REFERENCES public.session(id) ON DELETE CASCADE;


--
-- Name: verified_answers fk_session_verified_answers; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.verified_answers
    ADD CONSTRAINT fk_session_verified_answers FOREIGN KEY (session_id) REFERENCES public.session(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict Z3uIOQm9WpdPr3O6ePZBjQsdzeUx0xTakmYCHgEKjdEn9ygcREkQeUOH6G9n0AS

