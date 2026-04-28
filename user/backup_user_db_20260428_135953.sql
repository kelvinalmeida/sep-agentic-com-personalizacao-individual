--
-- PostgreSQL database dump
--

\restrict do5UEqi2seXbyvcLkaFg8nWzO6ipEG0IwpkXhvDL5Gtp2baISMmbIJUvR4s7DdG

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
-- Name: student; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.student (
    student_id integer NOT NULL,
    name character varying(100),
    course character varying(100),
    type character varying(20),
    age smallint,
    username character varying(80),
    email character varying(80),
    password_hash character varying(128),
    pref_content_type character varying(50),
    pref_communication character varying(50),
    pref_receive_email boolean
);


ALTER TABLE public.student OWNER TO "user";

--
-- Name: student_feedback; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.student_feedback (
    id integer NOT NULL,
    student_username character varying(100) NOT NULL,
    session_id integer,
    domain_name character varying(100),
    feedback_content text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.student_feedback OWNER TO "user";

--
-- Name: student_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.student_feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.student_feedback_id_seq OWNER TO "user";

--
-- Name: student_feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.student_feedback_id_seq OWNED BY public.student_feedback.id;


--
-- Name: student_student_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

ALTER TABLE public.student ALTER COLUMN student_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.student_student_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: teacher; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.teacher (
    teacher_id integer NOT NULL,
    name character varying(100),
    course character varying(100),
    type character varying(20),
    age smallint,
    username character varying(80),
    email character varying(80),
    password_hash character varying(128)
);


ALTER TABLE public.teacher OWNER TO "user";

--
-- Name: teacher_teacher_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

ALTER TABLE public.teacher ALTER COLUMN teacher_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.teacher_teacher_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tutor_chat_history; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.tutor_chat_history (
    id integer NOT NULL,
    student_username character varying(100) NOT NULL,
    sender character varying(20) NOT NULL,
    message text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tutor_chat_history OWNER TO "user";

--
-- Name: tutor_chat_history_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.tutor_chat_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tutor_chat_history_id_seq OWNER TO "user";

--
-- Name: tutor_chat_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.tutor_chat_history_id_seq OWNED BY public.tutor_chat_history.id;


--
-- Name: student_feedback id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.student_feedback ALTER COLUMN id SET DEFAULT nextval('public.student_feedback_id_seq'::regclass);


--
-- Name: tutor_chat_history id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.tutor_chat_history ALTER COLUMN id SET DEFAULT nextval('public.tutor_chat_history_id_seq'::regclass);


--
-- Data for Name: student; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.student (student_id, name, course, type, age, username, email, password_hash, pref_content_type, pref_communication, pref_receive_email) FROM stdin;
1	Kelvin	CC	student	22	kelvin	kelvin@email.com	hash	exemplos	chat	t
2	Maria	CC	student	21	maria	maria@email.com	hash	teoria	video	t
3	João	CC	student	23	joao	joao@email.com	hash	exercicios	video	f
4	Ana	CC	student	20	ana	ana@email.com	hash	exemplos	chat	t
5	Fabricio	CC	student	23	fabricio	dd	hash	teoria	chat	t
6	fatima	cc	student	22	fatima	cc	hash	teoria	chat	f
7	lucas	cc	student	33	lucas	cc	hash	exemplos	video	t
8	jose	cc	student	33	jose	cc	hash	exemplos	none	t
9	kelvinal	cc	student	22	paulo	cc	hash	teoria	video	t
10	Fernando Emídio Belfort do Rego	Engenharia de Computação	student	21	FernandoEBR	febr@ic.ufal.br	Fernando!26072004	teoria	chat	t
11	Antonio Eduardo	Ciência da computação	student	23	katochi	antonio.edu0507@gmail.com	edu.pedro753159	teoria	chat	f
12	Filipe Mota	Ciência da Computação	student	25	FilipeSMota	fsmota@ic.ufal.br	Macarenaudemy11	teoria	chat	t
13	Otávio Fernandes de Oliveira	Engenharia de Computação	student	20	otavio	otaviofernandes781@gmail.com	rbnfn781	exercicios	none	t
14	Giovanna Alves Barbosa de Oliveira	Engenharia de Computação	student	22	gabo2301	gabo@ic.ufal.br	camrendahmo	exemplos	none	t
15	Paulo Laercio de Oliveira Junior	Ciência da Computação	student	28	plaercio1812	plaerciojunior@gmail.com	pljr181297	teoria	chat	f
16	Jonatan Leite Alves	Ciência da Computação	student	32	JhonathanMilk	johnathanleitealves4@gmail.com	jlatecla	exemplos	none	f
17	Pedro Henrique Oliveira Neves	Engenharia de Computação	student	20	PedroNeves34	phon@ic.ufal.br	Pedro1goku	teoria	none	t
18	Alison Bruno Martires Soares	Engenharia de Computação	student	21	alisonbms	abms@ic.ufal.br	Ab20ms05	teoria	none	f
19	flavia	cc	student	23	flavia	dsasdasda	hash	teoria	chat	t
20	David Kelve Oliveira Barbosa	Engenharia de Computação	student	20	David Kelve Oliveira Barbosa	dkob@ic.ufal.br	dgcraft321tazergood	teoria	none	t
21	Larissa Ferreira Dias de Souza	EC	student	20	LarissaFDS	asdasdas	larissa1	exemplos	chat	f
22	Otávio Joshua Costa Brandão Menezes	Engenharia de Computação	student	21	Otavio	otaviomenezes574@gmail.com	otavio2004	teoria	chat	t
23	Marcelo Eduardo Pereira da Silva	Engenharia de computação	student	21	Marcelo	meps@ic.ufal.br	@Maredu132	exercicios	none	t
24	Luiz Henrique Lima Leite	Engenharia da Computação	student	23	Henriiqu_ee234	lhll@ic.ufal.br	sf13579@#	exemplos	none	t
25	Arthur Vinicius Alves	Engenharia de Computação 	student	20	Arthur	avas@ic.ufal.br	Arthur2020.	exercicios	none	f
26	Arthur Vinicius Alves	Engenharia de Computação 	student	20	arthuralves	avas@ic.ufal.br	Arthur2020.	exercicios	none	f
27	Fernando Gabriel Feitosa Leite	Ciência da Computação	student	22	fernandogfl	fgfl@ic.ufal.br	nandos2412@3210123#	exemplos	none	f
28	João Euclides da Silva melo	Engenharia de computação 	student	21	Jesm	jesm@ic.ufal.br	doqrir-vixRog-secny6	exemplos	none	t
29	Arthur	Engenharia de Computação	student	20	arthur.alves	avas@ic.ufal.br	Arthur	exercicios	none	t
30	LUIZ GUILHERME COUTINHO BRAZ	Ciência da Computação	student	23	GuiCoutinho	lgcb@ic.ufal.br	gui08052002*	exemplos	none	t
31	Tatiane	Ciencia da Computação	student	25	Tatiane	tma.@ic.ufal.br	Tati2020	teoria	none	f
32	Caio	Ciência da computação 	student	27	caiomascarenhas	cms@ic.ufal.br	soares10	exemplos	chat	f
33	Marcela Rocha 	Engenharia de computação 	student	20	Marrcela	mrs@ic.ufal.br	marcela07	teoria	none	f
34	Vítor Gabriel dos Santos Oliveira	Engenharia de computação	student	23	Vitor	vgso@ic.ufal.br	apenasJesussalva1#	exemplos	video	t
35	Henriqu_ee	Engenheira da computação 	student	23	Sf13579@#	lhll@ic.ufal.br	Sf13579@#	teoria	none	t
36	Lucas Cassiano	Ciência da Computação	student	21	lucas7maciel	lucasmacielcontato@gmail.com	120704Eu!	exercicios	chat	f
37	Riane Costa Santos	Engenharia de Computação 	student	22	riane_santos	rics@ic.ufal.br	Lifegoeson7@	exemplos	chat	t
38	LuizHenrique	Engenheira da computação 	student	23	Henriiqu_ee	luizhenrique20017x@gmail.com	sf13579@#	teoria	none	t
39	Lucas Fernando da Silva Português	Engenharia de Computação	student	24	Lucas_Portugues	lfspo@ic.ufal.br	portugues123	exemplos	none	f
40	Marcelo Eduardo Pereira da Silva	Engenharia de computação	student	21	Marcelo Eduardo Pereira da Silva	meps@ic.ufal.br	@Mar4edu132	exemplos	none	t
41	FILIPE SIMÕES MOTA	Ciência da Computação 	student	25	Fsmota12	filipesimoesmotao@gmail.com	Macarenaudemy11	teoria	chat	t
42	Marcos Douglas	Ciencia da computacao	student	25	marcosdouglas	mdsf@ic.ufal.br	123123123	exercicios	none	t
43	Marcelo Eduardo Pereira da Silva	Engenharia de computação	student	21	Marcelo Eduardo 2	marceloedu743@gmail.com	#mAREDU132	exemplos	none	t
44	Marcelo Eduardo Pereira da Silva	Engenharia de computação	student	21	Marcelo Eduardo	meps@ic.ufal.br	12345678	exemplos	none	t
\.


--
-- Data for Name: student_feedback; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.student_feedback (id, student_username, session_id, domain_name, feedback_content, created_at) FROM stdin;
\.


--
-- Data for Name: teacher; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.teacher (teacher_id, name, course, type, age, username, email, password_hash) FROM stdin;
1	kelvin123	\N	teacher	33	kelvin123	ksal@ic.ufal.br	88092018
2	Kelvin Santos	\N	teacher	31	kelvinsantos	kelvin	88092018
3	Arturo Hernández Domíinguez	\N	teacher	64	arturohd@uol.com.br	arturohd@uol.com.br	@Hd040795
\.


--
-- Data for Name: tutor_chat_history; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.tutor_chat_history (id, student_username, sender, message, created_at) FROM stdin;
\.


--
-- Name: student_feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.student_feedback_id_seq', 1, false);


--
-- Name: student_student_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.student_student_id_seq', 44, true);


--
-- Name: teacher_teacher_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.teacher_teacher_id_seq', 3, true);


--
-- Name: tutor_chat_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.tutor_chat_history_id_seq', 1, false);


--
-- Name: student_feedback student_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.student_feedback
    ADD CONSTRAINT student_feedback_pkey PRIMARY KEY (id);


--
-- Name: student student_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.student
    ADD CONSTRAINT student_pkey PRIMARY KEY (student_id);


--
-- Name: teacher teacher_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.teacher
    ADD CONSTRAINT teacher_pkey PRIMARY KEY (teacher_id);


--
-- Name: tutor_chat_history tutor_chat_history_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.tutor_chat_history
    ADD CONSTRAINT tutor_chat_history_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

\unrestrict do5UEqi2seXbyvcLkaFg8nWzO6ipEG0IwpkXhvDL5Gtp2baISMmbIJUvR4s7DdG

