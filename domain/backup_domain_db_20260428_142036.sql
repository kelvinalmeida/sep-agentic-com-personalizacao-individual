--
-- PostgreSQL database dump
--

\restrict RCg25vIkxLxhepT73diFLHsYp7xLZhcgo72n8BVsYl9h7Vq0VN8Wm2gn3Si83VE

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
-- Name: domain; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.domain (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    description text
);


ALTER TABLE public.domain OWNER TO "user";

--
-- Name: domain_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.domain_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.domain_id_seq OWNER TO "user";

--
-- Name: domain_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.domain_id_seq OWNED BY public.domain.id;


--
-- Name: exercise; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.exercise (
    id integer NOT NULL,
    question text NOT NULL,
    options jsonb NOT NULL,
    correct character varying(10) NOT NULL,
    domain_id integer NOT NULL
);


ALTER TABLE public.exercise OWNER TO "user";

--
-- Name: exercise_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.exercise_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.exercise_id_seq OWNER TO "user";

--
-- Name: exercise_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.exercise_id_seq OWNED BY public.exercise.id;


--
-- Name: pdf; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.pdf (
    id integer NOT NULL,
    filename character varying(255) NOT NULL,
    path character varying(255) NOT NULL,
    domain_id integer NOT NULL
);


ALTER TABLE public.pdf OWNER TO "user";

--
-- Name: pdf_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.pdf_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pdf_id_seq OWNER TO "user";

--
-- Name: pdf_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.pdf_id_seq OWNED BY public.pdf.id;


--
-- Name: rag_library; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.rag_library (
    id integer NOT NULL,
    filename character varying(255) NOT NULL,
    path character varying(500) NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.rag_library OWNER TO "user";

--
-- Name: rag_library_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.rag_library_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rag_library_id_seq OWNER TO "user";

--
-- Name: rag_library_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.rag_library_id_seq OWNED BY public.rag_library.id;


--
-- Name: video_upload; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.video_upload (
    id integer NOT NULL,
    filename character varying(255) NOT NULL,
    path character varying(255) NOT NULL,
    domain_id integer NOT NULL
);


ALTER TABLE public.video_upload OWNER TO "user";

--
-- Name: video_upload_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.video_upload_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.video_upload_id_seq OWNER TO "user";

--
-- Name: video_upload_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.video_upload_id_seq OWNED BY public.video_upload.id;


--
-- Name: video_youtube; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.video_youtube (
    id integer NOT NULL,
    url character varying(500) NOT NULL,
    domain_id integer NOT NULL
);


ALTER TABLE public.video_youtube OWNER TO "user";

--
-- Name: video_youtube_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.video_youtube_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.video_youtube_id_seq OWNER TO "user";

--
-- Name: video_youtube_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.video_youtube_id_seq OWNED BY public.video_youtube.id;


--
-- Name: domain id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.domain ALTER COLUMN id SET DEFAULT nextval('public.domain_id_seq'::regclass);


--
-- Name: exercise id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.exercise ALTER COLUMN id SET DEFAULT nextval('public.exercise_id_seq'::regclass);


--
-- Name: pdf id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pdf ALTER COLUMN id SET DEFAULT nextval('public.pdf_id_seq'::regclass);


--
-- Name: rag_library id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.rag_library ALTER COLUMN id SET DEFAULT nextval('public.rag_library_id_seq'::regclass);


--
-- Name: video_upload id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.video_upload ALTER COLUMN id SET DEFAULT nextval('public.video_upload_id_seq'::regclass);


--
-- Name: video_youtube id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.video_youtube ALTER COLUMN id SET DEFAULT nextval('public.video_youtube_id_seq'::regclass);


--
-- Data for Name: domain; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.domain (id, name, description) FROM stdin;
1	Fremeworks	Como aprender um framework?\nPor isso, vamos abordar neste artigo alguns pontos sobre quando é o momento ideal para se aventurar nos frameworks.\n\n    Construa primeiro uma base sólida na linguagem. ...\n    Tente resolver problemas sem utilizar frameworks. ...\n    Identifique a necessidade. ...\n    Não se esqueça do equilíbrio
2	C++	C++ é uma linguagem de programação poderosa, de propósito geral e de alto desempenho, criada como uma extensão da linguagem C, oferecendo controle de baixo nível sobre o hardware e suporte multi-paradigma (orientada a objetos, genérica, imperativa).
21	Aula 01 - Microservices no nível Básico	As aulas apresentam primeiro a base teórica dos microsserviços e depois mostram sua aplicação prática com Flask.\r\nNa parte teórica, é explicado que a arquitetura monolítica concentra tudo em um único sistema, enquanto os microsserviços dividem a aplicação em serviços menores e independentes.\r\nEssa divisão reduz o acoplamento, melhora a escalabilidade e permite que falhas em um serviço não derrubem todo o sistema.\r\nTambém é destacado que cada microserviço possui sua própria responsabilidade e, em muitos casos, seu próprio banco de dados.\r\nA comunicação entre esses serviços ocorre principalmente por meio de APIs usando HTTP/REST e troca de dados em JSON.\r\nNa parte prática, a aula utiliza Flask por sua simplicidade para criar APIs pequenas e independentes, cada uma rodando em uma porta diferente.\r\nO primeiro exemplo mostra um sistema de biblioteca com serviços de livros, usuários e empréstimo, em que o empréstimo atua como orquestrador.\r\nO segundo exemplo apresenta um e-commerce com serviços de catálogo, estoque, pagamento e checkout, simulando um fluxo real de compra.\r\nAlém dos conceitos, a aula ensina a criar ambiente virtual, instalar dependências como Flask e requests, executar os serviços e testar as rotas.\r\nNo conjunto, as duas aulas mostram tanto o conceito quanto a implementação de microsserviços, unindo teoria, organização arquitetural e prática de desenvolvimento. 
24	Aula 02 - Microservices no nível Intermediário	
\.


--
-- Data for Name: exercise; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.exercise (id, question, options, correct, domain_id) FROM stdin;
1	Em frameworks front-end modernos (como React, Vue ou Angular), o conceito de "reatividade" é central. Qual das alternativas abaixo descreve corretamente o comportamento de um framework reativo ao detectar uma mudança no estado (state) de um componente?	["O framework exige que o desenvolvedor recarregue a página manualmente.", "O framework atualiza automaticamente apenas as partes da interface (DOM) que dependem daquele estado.", "O framework apaga o componente e cria um novo do zero, perdendo dados não salvos.", "O framework converte o código para HTML estático e para de responder a eventos."]	1	1
2	Ao utilizar frameworks de back-end como Spring Boot (Java) ou NestJS (Node.js) para criar APIs REST, o desenvolvedor frequentemente utiliza "Decorators" ou "Annotations" (ex: @GetMapping, @Post). Qual é a principal função desse recurso?	["Apenas comentar o código para documentação.", "Configurar metadados, como rotas, injeção de dependência e validações, de forma declarativa.", "Aumentar a performance do processador do servidor.", "Substituir a necessidade de escrever classes e funções."]	1	1
3	Frameworks de estilização como o Tailwind CSS ganharam muita popularidade em 2024 e 2025. Qual é a característica principal da abordagem "Utility-First" proposta por esse tipo de ferramenta?	["O uso de classes utilitárias de baixo nível que permitem construir designs diretamente no HTML.", "A obrigatoriedade de escrever arquivos CSS separados para cada componente.", "O fornecimento de componentes prontos (como botões e navbars) idênticos ao Bootstrap.", "A proibição do uso de design responsivo."]	0	1
4	Qual será a saída do seguinte trecho de código em C++: cout << 10 + 20;	["1020", "30", "Erro de compilação", "0"]	1	2
5	No contexto de Programação Orientada a Objetos em C++, o que define uma classe abstrata?	["Uma classe que não possui construtor.", "Uma classe que possui apenas atributos privados.", "Uma classe que não pode ser instanciada diretamente e possui pelo menos uma função virtual pura.", "Uma classe que herda de múltiplas classes base."]	2	2
6	Considere o uso de Smart Pointers (Ponteiros Inteligentes) introduzidos a partir do C++11. Qual das alternativas descreve corretamente o comportamento do std::unique_ptr?	["Permite que múltiplos ponteiros apontem para o mesmo objeto simultaneamente.", "Gerencia a memória automaticamente garantindo posse (ownership) exclusiva de um recurso.", "Não libera a memória automaticamente, exigindo o uso de delete.", "É utilizado apenas para array de caracteres."]	1	2
9	Em um sistema de microsserviços, o Gateway atua como único ponto de entrada para o cliente. Qual das alternativas abaixo descreve melhor o papel que ele desempenha nessa arquitetura?	["Ele substitui todos os outros serviços, centralizando toda a lógica de negócio em um único lugar", "Ele armazena os dados de todos os serviços para evitar que o cliente precise fazer múltiplas requisições", "Ele recebe a requisição do cliente, consulta os serviços necessários, agrega as respostas e entrega tudo pronto, sem que o cliente saiba que outros serviços existem", "Ele funciona apenas como uma camada de segurança, bloqueando acessos não autorizados sem interagir com os demais serviços", "Ele distribui o processamento igualmente entre todos os serviços disponíveis, independentemente do tipo de requisição"]	2	24
10	A aula apresenta o conceito de container comparando-o a um container de navio. Qual é o problema do mundo real do desenvolvimento de software que essa analogia busca explicar?	["A dificuldade de escrever código que funcione em diferentes linguagens de programação ao mesmo tempo", "A lentidão causada por aplicações que consomem muita memória RAM durante a execução", "O fato de um código funcionar perfeitamente em uma máquina e falhar em outra por diferenças de ambiente, como versões de bibliotecas ou do Python", "A impossibilidade de dois desenvolvedores trabalharem no mesmo projeto simultaneamente sem conflitos", "A falta de segurança em aplicações web que ficam expostas diretamente na internet sem proteção"]	2	24
11	Segundo a aula, o Dockerfile é descrito como uma "receita de bolo". O que essa analogia comunica sobre o papel desse arquivo dentro do ecossistema Docker?	["Que o Dockerfile é um arquivo opcional, usado apenas quando se quer personalizar o ambiente além do padrão", "Que o Dockerfile contém as instruções passo a passo que o Docker deve seguir para preparar o ambiente completo da aplicação", "Que o Dockerfile é executado automaticamente toda vez que o container é iniciado, atualizando as dependências", "Que o Dockerfile define apenas as variáveis de ambiente e as portas que o serviço vai utilizar", "Que o Dockerfile é compartilhado entre todos os serviços de um projeto, centralizando as configurações em um único lugar"]	1	24
12	A aula diferencia os conceitos de imagem e container no Docker usando uma analogia da orientação a objetos. Com base nessa diferenciação conceitual, o que representa cada um?	["A imagem é o container já em execução; o container é o histórico de todas as imagens geradas anteriormente", "A imagem é o resultado final da aplicação rodando; o container é o ambiente isolado que a encapsula", "A imagem é um arquivo de backup do sistema; o container é a versão ativa e atualizada desse backup", "A imagem é o molde com tudo que a aplicação precisa para rodar; o container é uma instância ativa gerada a partir desse molde", "A imagem e o container são equivalentes, diferindo apenas no momento do ciclo de vida em que se encontram"]	3	24
13	A aula explica que containers Docker precisam de uma rede para se comunicar. Por que isso é necessário, e o que aconteceria sem ela?	[" Sem uma rede, os containers consumiriam mais memória, tornando o sistema mais lento", "Sem uma rede, os containers não conseguiriam acessar a internet para baixar atualizações de bibliotecas", "Sem uma rede, cada container ficaria isolado no seu próprio ambiente, sem conseguir se comunicar com os outros containers do sistema", "Sem uma rede, o Docker não conseguiria distinguir quais containers pertencem ao mesmo projeto", "Sem uma rede, o Dockerfile não seria executado corretamente durante a criação das imagens"]	2	24
\.


--
-- Data for Name: pdf; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.pdf (id, filename, path, domain_id) FROM stdin;
1	Paper-2024-AgentDesignPatternCatalogue.pdf	https://f32aymnyqlp1vubu.public.blob.vercel-storage.com/Paper-2024-AgentDesignPatternCatalogue.pdf	1
2	Paper-Agents-2024-Ignise.pdf	https://f32aymnyqlp1vubu.public.blob.vercel-storage.com/Paper-Agents-2024-Ignise.pdf	1
3	Le_Prototype_BIRDS.pdf	https://f32aymnyqlp1vubu.public.blob.vercel-storage.com/Le_Prototype_BIRDS.pdf	2
4	Relatorio_Reuso-comLinkVideo.pdf	https://f32aymnyqlp1vubu.public.blob.vercel-storage.com/Relatorio_Reuso-comLinkVideo.pdf	2
23	Aula01_Teoria_Microservices_compressed.pdf	uploads/Aula01_Teoria_Microservices_compressed.pdf	21
24	Aula-02-Microservicos-na-Pratica-com-Flask-2_compressed.pdf	uploads/Aula-02-Microservicos-na-Pratica-com-Flask-2_compressed.pdf	21
27	Aula_03__Gateway_orquestrador_e_container_com_docker-2_compressed_1.pdf	uploads/Aula_03__Gateway_orquestrador_e_container_com_docker-2_compressed_1.pdf	24
\.


--
-- Data for Name: rag_library; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.rag_library (id, filename, path, description, created_at) FROM stdin;
1	Padrão Pedagogico-SessaoEnsino-FA_PorT-SBIE2007-LEASPE.pdf	https://f32aymnyqlp1vubu.public.blob.vercel-storage.com/Padr%C3%A3o%20Pedagogico-SessaoEnsino-FA_PorT-SBIE2007-LEASPE.pdf	Artigo sobre estratégias de ensino de IA: recomenda uso de Debate Sincrono para fixação e Reuso de materiais. A nota deve valorizar a interatividade.	2026-04-19 00:31:16.025623
2	Execucao de uma Sessao de Ensino.pdf	https://f32aymnyqlp1vubu.public.blob.vercel-storage.com/Execucao%20de%20uma%20Sessao%20de%20Ensino.pdf	Uma sessão de ensino contem uma estratégia e cada estratégia é composta de varias táticas.	2026-04-19 00:31:16.025623
\.


--
-- Data for Name: video_upload; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.video_upload (id, filename, path, domain_id) FROM stdin;
1	2025-12-19_09-57-13.mp4	https://f32aymnyqlp1vubu.public.blob.vercel-storage.com/2025-12-19_09-57-13.mp4	1
2	2025-12-19_10-13-32.mp4	https://f32aymnyqlp1vubu.public.blob.vercel-storage.com/2025-12-19_10-13-32.mp4	2
\.


--
-- Data for Name: video_youtube; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.video_youtube (id, url, domain_id) FROM stdin;
1	https://www.youtube.com/watch?v=BQ35b4b8qi4&t=616s	1
2	https://www.youtube.com/watch?v=MQUP3ML8Sjs	1
3	https://www.youtube.com/watch?v=N-VMAIvm3W4	2
4	https://www.youtube.com/watch?v=4p7axLXXBGU	2
\.


--
-- Name: domain_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.domain_id_seq', 24, true);


--
-- Name: exercise_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.exercise_id_seq', 13, true);


--
-- Name: pdf_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.pdf_id_seq', 27, true);


--
-- Name: rag_library_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.rag_library_id_seq', 2, true);


--
-- Name: video_upload_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.video_upload_id_seq', 2, true);


--
-- Name: video_youtube_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.video_youtube_id_seq', 4, true);


--
-- Name: domain domain_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.domain
    ADD CONSTRAINT domain_pkey PRIMARY KEY (id);


--
-- Name: exercise exercise_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.exercise
    ADD CONSTRAINT exercise_pkey PRIMARY KEY (id);


--
-- Name: pdf pdf_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pdf
    ADD CONSTRAINT pdf_pkey PRIMARY KEY (id);


--
-- Name: rag_library rag_library_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.rag_library
    ADD CONSTRAINT rag_library_pkey PRIMARY KEY (id);


--
-- Name: video_upload video_upload_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.video_upload
    ADD CONSTRAINT video_upload_pkey PRIMARY KEY (id);


--
-- Name: video_youtube video_youtube_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.video_youtube
    ADD CONSTRAINT video_youtube_pkey PRIMARY KEY (id);


--
-- Name: exercise fk_domain_exercise; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.exercise
    ADD CONSTRAINT fk_domain_exercise FOREIGN KEY (domain_id) REFERENCES public.domain(id) ON DELETE CASCADE;


--
-- Name: pdf fk_domain_pdf; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.pdf
    ADD CONSTRAINT fk_domain_pdf FOREIGN KEY (domain_id) REFERENCES public.domain(id) ON DELETE CASCADE;


--
-- Name: video_upload fk_domain_video_upload; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.video_upload
    ADD CONSTRAINT fk_domain_video_upload FOREIGN KEY (domain_id) REFERENCES public.domain(id) ON DELETE CASCADE;


--
-- Name: video_youtube fk_domain_video_youtube; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.video_youtube
    ADD CONSTRAINT fk_domain_video_youtube FOREIGN KEY (domain_id) REFERENCES public.domain(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict RCg25vIkxLxhepT73diFLHsYp7xLZhcgo72n8BVsYl9h7Vq0VN8Wm2gn3Si83VE

