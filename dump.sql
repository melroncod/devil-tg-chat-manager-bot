--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

-- Started on 2025-05-28 02:47:19

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
-- TOC entry 218 (class 1259 OID 16429)
-- Name: admins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.admins (
    user_id bigint NOT NULL
);


ALTER TABLE public.admins OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 16549)
-- Name: bans; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bans (
    user_id bigint NOT NULL,
    chat_id bigint NOT NULL,
    ban_count integer DEFAULT 0 NOT NULL,
    last_ban timestamp without time zone,
    username text
);


ALTER TABLE public.bans OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16526)
-- Name: chat_rules; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_rules (
    chat_id bigint NOT NULL,
    rules text NOT NULL
);


ALTER TABLE public.chat_rules OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 16421)
-- Name: chats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chats (
    chat_id bigint NOT NULL,
    name text NOT NULL,
    member_count integer DEFAULT 0
);


ALTER TABLE public.chats OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16457)
-- Name: filters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.filters (
    chat_id bigint NOT NULL,
    links_enabled boolean DEFAULT true NOT NULL,
    caps_enabled boolean DEFAULT false NOT NULL,
    spam_enabled boolean DEFAULT false NOT NULL,
    swear_enabled boolean DEFAULT false NOT NULL,
    keywords_enabled boolean DEFAULT false NOT NULL,
    stickers_enabled boolean DEFAULT false NOT NULL,
    join_delete_enabled boolean DEFAULT false NOT NULL
);


ALTER TABLE public.filters OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 16495)
-- Name: keywords; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.keywords (
    chat_id bigint NOT NULL,
    keyword text NOT NULL
);


ALTER TABLE public.keywords OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 16533)
-- Name: log_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.log_settings (
    chat_id bigint NOT NULL,
    log_chat_id bigint,
    is_logging_enabled boolean DEFAULT false NOT NULL
);


ALTER TABLE public.log_settings OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16482)
-- Name: mutes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mutes (
    user_id bigint NOT NULL,
    chat_id bigint NOT NULL,
    mute_count integer DEFAULT 0 NOT NULL,
    last_mute timestamp without time zone,
    username text
);


ALTER TABLE public.mutes OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16507)
-- Name: user_aliases; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_aliases (
    chat_id bigint NOT NULL,
    username text NOT NULL,
    user_id bigint NOT NULL
);


ALTER TABLE public.user_aliases OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16441)
-- Name: user_chats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_chats (
    user_id bigint NOT NULL,
    chat_id bigint NOT NULL,
    first_seen timestamp without time zone NOT NULL,
    last_seen timestamp without time zone NOT NULL,
    message_count integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.user_chats OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16434)
-- Name: user_info; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_info (
    user_id bigint NOT NULL,
    username text,
    first_name text,
    last_name text,
    last_seen timestamp without time zone
);


ALTER TABLE public.user_info OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 16469)
-- Name: warnings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.warnings (
    user_id bigint NOT NULL,
    chat_id bigint NOT NULL,
    warn_count integer DEFAULT 0 NOT NULL,
    last_warn timestamp without time zone,
    username text
);


ALTER TABLE public.warnings OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 16519)
-- Name: welcome_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.welcome_messages (
    chat_id bigint NOT NULL,
    message text NOT NULL
);


ALTER TABLE public.welcome_messages OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 16544)
-- Name: welcome_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.welcome_settings (
    chat_id bigint NOT NULL,
    delete_timeout integer NOT NULL
);


ALTER TABLE public.welcome_settings OWNER TO postgres;

--
-- TOC entry 4887 (class 0 OID 16429)
-- Dependencies: 218
-- Data for Name: admins; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.admins (user_id) FROM stdin;
863424729
6263778247
\.


--
-- TOC entry 4899 (class 0 OID 16549)
-- Dependencies: 230
-- Data for Name: bans; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bans (user_id, chat_id, ban_count, last_ban, username) FROM stdin;
7218007856	-1002653793518	0	\N	loyfferych
\.


--
-- TOC entry 4896 (class 0 OID 16526)
-- Dependencies: 227
-- Data for Name: chat_rules; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chat_rules (chat_id, rules) FROM stdin;
-1002248129649	Правила крутые
-1002636434179	Уважать всех мяувочек
-1002653793518	1. Уважать админов\n2. Пить чай
\.


--
-- TOC entry 4886 (class 0 OID 16421)
-- Dependencies: 217
-- Data for Name: chats; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chats (chat_id, name, member_count) FROM stdin;
-1002653793518	АВГАН ПУШИСТИКИ 2	0
-1002585249434	etteet	0
-1002534811183	Ddd	0
-1002406686999	Random Tea Store	0
-1002366999382	Old ghetto DYS💅🏿	0
-1002248129649	Test Chanel Chat	0
-1002220889183	чат Фан клуб башаме	0
-1002636434179	Test gr	0
\.


--
-- TOC entry 4890 (class 0 OID 16457)
-- Dependencies: 221
-- Data for Name: filters; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.filters (chat_id, links_enabled, caps_enabled, spam_enabled, swear_enabled, keywords_enabled, stickers_enabled, join_delete_enabled) FROM stdin;
-1002585249434	t	t	t	t	f	f	f
-1002534811183	t	t	t	t	t	t	f
-1002406686999	t	t	t	t	f	t	t
-1002366999382	f	f	f	f	f	f	f
-1002220889183	t	t	t	t	f	f	f
-1002653793518	f	t	t	t	t	t	f
-1002248129649	t	t	t	t	f	t	t
-1002636434179	t	t	t	t	t	t	t
\.


--
-- TOC entry 4893 (class 0 OID 16495)
-- Dependencies: 224
-- Data for Name: keywords; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.keywords (chat_id, keyword) FROM stdin;
-1002534811183	матьсдохла
-1002534811183	как же круто учиться в горном
-1002653793518	как же круто учиться в горном
-1002653793518	берестова самый крутой препод
-1002653793518	джоджо мусор
-1002248129649	кикимора
-1002636434179	бебра
\.


--
-- TOC entry 4897 (class 0 OID 16533)
-- Dependencies: 228
-- Data for Name: log_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.log_settings (chat_id, log_chat_id, is_logging_enabled) FROM stdin;
-1002653793518	-1001718310191	t
-1002406686999	-1001718310191	t
-1002248129649	-1001718310191	t
-1002636434179	-1001718310191	t
\.


--
-- TOC entry 4892 (class 0 OID 16482)
-- Dependencies: 223
-- Data for Name: mutes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mutes (user_id, chat_id, mute_count, last_mute, username) FROM stdin;
1087968824	-1002248129649	7	2025-05-04 15:38:57.605602	GroupAnonymousBot
6263778247	-1002248129649	4	2025-04-21 16:34:21.403514	\N
7510343390	-1002248129649	1	2025-04-21 16:42:19.147628	\N
7510343390	-1002534811183	0	\N	jrdcmal
6311557300	-1002653793518	5	2025-04-28 17:48:34.296793	Murmanskun
863424729	-1002534811183	0	2025-04-28 08:43:54.105242	melron27
1188955540	-1002653793518	0	2025-04-28 17:48:34.278792	tripleflex
863424729	-1002653793518	2	2025-04-28 18:49:31.182872	melron27
777000	-1002248129649	2	2025-05-12 12:10:01.339423	Telegram
1676714476	-1002366999382	4	2025-05-18 05:00:36.69763	Geraskin Alexander
965951655	-1002366999382	0	2025-05-06 05:03:52.156423	AnastasiaZwww
1028668005	-1002366999382	0	2025-05-07 17:53:33.842121	VELIKIJMAO
791504494	-1002366999382	0	2025-05-08 04:42:16.242881	gengholdonbang
1672595832	-1002366999382	0	2025-05-09 03:44:31.17448	MistyForce
1400783973	-1002366999382	0	2025-05-14 04:55:22.989879	trtrtr101
991493893	-1002366999382	0	2025-05-14 05:02:45.317898	mefffchik3
858492242	-1002366999382	0	2025-05-16 18:17:45.58443	fintoplushka
1918938717	-1002366999382	0	2025-05-16 18:22:50.55352	cumshotfromdick
7510343390	-1002636434179	2	2025-05-27 20:43:32.154866	jrdcmal
7218007856	-1002653793518	0	\N	loyfferych
\.


--
-- TOC entry 4894 (class 0 OID 16507)
-- Dependencies: 225
-- Data for Name: user_aliases; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_aliases (chat_id, username, user_id) FROM stdin;
-1002534811183	melron27	863424729
-1002534811183	jrdcmal	7510343390
-1002653793518	melron27	863424729
-1002653793518	tripleflex	1188955540
-1002248129649	jrdcmal	7510343390
-1002248129649	groupanonymousbot	1087968824
-1002636434179	jrdcmal	7510343390
-1002653793518	loyfferych	7218007856
\.


--
-- TOC entry 4889 (class 0 OID 16441)
-- Dependencies: 220
-- Data for Name: user_chats; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_chats (user_id, chat_id, first_seen, last_seen, message_count) FROM stdin;
863424729	-1002248129649	2025-05-27 17:56:16.470253	2025-05-27 17:56:16.470253	0
7218007856	-1002220889183	2025-05-27 17:56:16.470253	2025-05-27 17:56:16.470253	0
6263778247	-1002534811183	2025-04-28 18:42:01.654382	2025-04-28 18:42:01.654382	0
863424729	-1002653793518	2025-04-28 18:42:43.59493	2025-04-28 18:42:43.59493	0
1088670014	-1002366999382	2025-05-08 04:43:55.919925	2025-05-08 04:43:55.919925	0
863424729	-1002406686999	2025-05-08 21:22:47.41827	2025-05-08 21:22:47.41827	0
863424729	-1002636434179	2025-05-27 19:01:38.866235	2025-05-27 19:01:38.866235	0
\.


--
-- TOC entry 4888 (class 0 OID 16434)
-- Dependencies: 219
-- Data for Name: user_info; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_info (user_id, username, first_name, last_name, last_seen) FROM stdin;
863424729	\N	\N	\N	\N
7218007856	\N	\N	\N	\N
6263778247	\N	\N	\N	\N
1088670014	\N	\N	\N	\N
1087968824	\N	\N	\N	\N
7510343390	\N	\N	\N	\N
1297596347	\N	\N	\N	\N
777000	\N	\N	\N	\N
136817688	\N	\N	\N	\N
1657644565	\N	\N	\N	\N
6311557300	\N	\N	\N	\N
1188955540	\N	\N	\N	\N
1676714476	\N	\N	\N	\N
965951655	\N	\N	\N	\N
1028668005	\N	\N	\N	\N
791504494	\N	\N	\N	\N
1672595832	\N	\N	\N	\N
1400783973	\N	\N	\N	\N
991493893	\N	\N	\N	\N
858492242	\N	\N	\N	\N
1918938717	\N	\N	\N	\N
\.


--
-- TOC entry 4891 (class 0 OID 16469)
-- Dependencies: 222
-- Data for Name: warnings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.warnings (user_id, chat_id, warn_count, last_warn, username) FROM stdin;
6263778247	-1002585249434	0	2025-04-28 09:31:30.600113	geronimostilson
7218007856	-1002653793518	2	2025-05-16 04:40:28.654339	loyfferych
7510343390	-1002534811183	2	2025-05-04 19:26:18.107142	jrdcmal
1297596347	-1002653793518	2	2025-05-04 21:31:18.587346	huesosik12
777000	-1002220889183	1	2025-05-05 19:58:59.670633	Telegram
136817688	-1002220889183	1	2025-05-07 09:35:55.532504	Channel_Bot
1657644565	-1002366999382	1	2025-05-17 17:09:57.620783	qqmercury
\.


--
-- TOC entry 4895 (class 0 OID 16519)
-- Dependencies: 226
-- Data for Name: welcome_messages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.welcome_messages (chat_id, message) FROM stdin;
-1002585249434	Привет, {username}!
-1002534811183	Привет, {username}!
-1002406686999	Привет, {username}!\nДобро пожаловать в наше чайное сообщество {chat_title}!\n\nРасскажи немного о себе — откуда ты, как пришёл к чаю, какие вкусы тебе ближе: пуэр, улун, шен, может, красный?\nЗдесь можно делиться фото, впечатлениями, задавать вопросы и просто общаться на чайные (и не только) темы. Располагайся как дома!
-1002366999382	Давайте поприветствуем нового сотрудника нашей территории {username}\n\nДобро пожаловать🤝🏻💪🏻\nИ\nWellcum to the club body\n\nПизделка - сервер почти что неограниченной анархии, мемов, шуток, бомбежа на клиентов и вообще всего, что тебе вздумается. Чернуха иногда даже приветствуется))\n\nНас посещал - сюда мы кратенько пишем кто из вышестоящих сотрудников (выше управляющего по должности) к тебе на точку приезжал, на что обращал внимание, до чего докапывался. Это сделано для того, чтобы за счет первых жертв остальные магазины могли исправить косяки и не получить пиздюлей\n\nФорма - тут отчитываемся о состоянии рецепции, вывески, штендеров, музыки и своего внешнего вида\n\nВажные сообщения - ты не поверишь... ЭТО ВАЖНО. Всё читать, слушать, всё усваивать\n\nУборка - чат, где ты отчитываешься об исправлении косяков, которые обнаружили на твоём магазине(временно упразднен, но может вернуться)\n\nПеремещения основы - здесь пишутся все перемещения, которые производятся с товаром ТОЛЬКО на основных магазинах. Товар с основ на франшизы и наоборот перемещать нельзя\n\nПолезные ссылки - ну тут интуитивно понятно, можешь тут найти что-то, что поможет тебе работать\n\nЗаявки на товар - сюда кидаем заявку перед отправкой на склад. Нужно, в основном как облачное хранилище. Но не забывай отправить Левлу (его номер есть в закрепе этого чата)\n\nХозки - каждую вторую субботу тут просим всякие хозяйственные штуки по типу тряпок, стекломойки, чековой ленты, туалетной бумаги, мусорных пакетов и прочих расходников, необходимых для работы\n\nНовости и новинки - очевидно что там. За этим чатом тоже поглядывай и запоминай, чтобы в случае любого вопроса ты мог быстро и четко ответить\n\nСюда же можем отнести \nТема «Территория Ильи»:\nСостав - сюда отписываем с 20:00 до 20:30 точку, на которую завтра выходишь и все замены, которые происходят. \n\nВажная информация\n- иногда туда я скидываю заявку на будущую неделю. \n\nДля Феди и Ани - там отдел кадров пишет важную информацию. \n\nПовторюсь \nВсе чаты в этой теме, за исключением «важная информация» и «новинки» можете сразу заглушить, чтобы не надоедали уведы\n\nТему «Территория Ильи», чаты «важная информация» и «новинки» глушить нельзя ни в коем случае\n\nБудем знакомы, меня Илья зовут и я управ @metandi\n\nЕсли что не понятно - обязательно спрашивайте, лучше потратить немного времени на правильное решение, чем потратить много денег на оплату штрафа или разгребать последствия\n\n{first_name} смотри, я человек и у меня есть выходные, а так же много задач. Поэтому у меня есть помощники - это @dm_elizaveta и @kooki_9769 \nПоэтому если они пишут тебе замечания или же журят как-то, не пугайся и слушай их. Считай, что вещаю я и делаю замечания я. Ну и велком🫶🏻
-1002248129649	Привет, {username}!\nДобро пожаловать в наше чайное сообщество {chat_title}!\n\nРасскажи немного о себе — откуда ты, как пришёл к чаю, какие вкусы тебе ближе: пуэр, улун, шен, может, красный?\nЗдесь можно делиться фото, впечатлениями, задавать вопросы и просто общаться на чайные (и не только) темы. Располагайся как дома!
-1002636434179	Привет, мявка {username}❤️
-1002653793518	Э, {username}, ты кто такой и нафиг сюда зашёл?!?!?!
\.


--
-- TOC entry 4898 (class 0 OID 16544)
-- Dependencies: 229
-- Data for Name: welcome_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.welcome_settings (chat_id, delete_timeout) FROM stdin;
-1002534811183	5
-1002406686999	600
-1002636434179	5
\.


--
-- TOC entry 4708 (class 2606 OID 16433)
-- Name: admins admins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_pkey PRIMARY KEY (user_id);


--
-- TOC entry 4732 (class 2606 OID 16556)
-- Name: bans bans_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bans
    ADD CONSTRAINT bans_pkey PRIMARY KEY (user_id, chat_id);


--
-- TOC entry 4726 (class 2606 OID 16532)
-- Name: chat_rules chat_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_rules
    ADD CONSTRAINT chat_rules_pkey PRIMARY KEY (chat_id);


--
-- TOC entry 4706 (class 2606 OID 16428)
-- Name: chats chats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chats
    ADD CONSTRAINT chats_pkey PRIMARY KEY (chat_id);


--
-- TOC entry 4714 (class 2606 OID 16468)
-- Name: filters filters_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.filters
    ADD CONSTRAINT filters_pkey PRIMARY KEY (chat_id);


--
-- TOC entry 4720 (class 2606 OID 16501)
-- Name: keywords keywords_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.keywords
    ADD CONSTRAINT keywords_pkey PRIMARY KEY (chat_id, keyword);


--
-- TOC entry 4728 (class 2606 OID 16538)
-- Name: log_settings log_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.log_settings
    ADD CONSTRAINT log_settings_pkey PRIMARY KEY (chat_id);


--
-- TOC entry 4718 (class 2606 OID 16489)
-- Name: mutes mutes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mutes
    ADD CONSTRAINT mutes_pkey PRIMARY KEY (user_id, chat_id);


--
-- TOC entry 4722 (class 2606 OID 16513)
-- Name: user_aliases user_aliases_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_aliases
    ADD CONSTRAINT user_aliases_pkey PRIMARY KEY (chat_id, username);


--
-- TOC entry 4712 (class 2606 OID 16446)
-- Name: user_chats user_chats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_chats
    ADD CONSTRAINT user_chats_pkey PRIMARY KEY (user_id, chat_id);


--
-- TOC entry 4710 (class 2606 OID 16440)
-- Name: user_info user_info_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_info
    ADD CONSTRAINT user_info_pkey PRIMARY KEY (user_id);


--
-- TOC entry 4716 (class 2606 OID 16476)
-- Name: warnings warnings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.warnings
    ADD CONSTRAINT warnings_pkey PRIMARY KEY (user_id, chat_id);


--
-- TOC entry 4724 (class 2606 OID 16525)
-- Name: welcome_messages welcome_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.welcome_messages
    ADD CONSTRAINT welcome_messages_pkey PRIMARY KEY (chat_id);


--
-- TOC entry 4730 (class 2606 OID 16548)
-- Name: welcome_settings welcome_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.welcome_settings
    ADD CONSTRAINT welcome_settings_pkey PRIMARY KEY (chat_id);


--
-- TOC entry 4740 (class 2606 OID 16557)
-- Name: bans bans_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bans
    ADD CONSTRAINT bans_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(chat_id) ON DELETE CASCADE;


--
-- TOC entry 4737 (class 2606 OID 16502)
-- Name: keywords keywords_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.keywords
    ADD CONSTRAINT keywords_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(chat_id) ON DELETE CASCADE;


--
-- TOC entry 4739 (class 2606 OID 16539)
-- Name: log_settings log_settings_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.log_settings
    ADD CONSTRAINT log_settings_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(chat_id) ON DELETE CASCADE;


--
-- TOC entry 4736 (class 2606 OID 16490)
-- Name: mutes mutes_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mutes
    ADD CONSTRAINT mutes_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(chat_id) ON DELETE CASCADE;


--
-- TOC entry 4738 (class 2606 OID 16514)
-- Name: user_aliases user_aliases_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_aliases
    ADD CONSTRAINT user_aliases_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(chat_id) ON DELETE CASCADE;


--
-- TOC entry 4733 (class 2606 OID 16452)
-- Name: user_chats user_chats_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_chats
    ADD CONSTRAINT user_chats_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(chat_id) ON DELETE CASCADE;


--
-- TOC entry 4734 (class 2606 OID 16447)
-- Name: user_chats user_chats_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_chats
    ADD CONSTRAINT user_chats_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_info(user_id) ON DELETE CASCADE;


--
-- TOC entry 4735 (class 2606 OID 16477)
-- Name: warnings warnings_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.warnings
    ADD CONSTRAINT warnings_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(chat_id) ON DELETE CASCADE;


-- Completed on 2025-05-28 02:47:19

--
-- PostgreSQL database dump complete
--

