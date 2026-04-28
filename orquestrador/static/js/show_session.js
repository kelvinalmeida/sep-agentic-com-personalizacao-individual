document.addEventListener("DOMContentLoaded", () => {
    let countdownInterval = null;
    let taticaAtiva = false;
    let adaptiveTacticEnabled = false;

    let debateSicrono_isActive = false;
    let apresentacaoSicrona_isActive = false;
    let reuso_isActive = false;
    let envio_informacao_isActive = false;
    let regras_isActive = false;
    let current_tatic_description = 'Nenhuma tática ativa no momento.';
    let activeTacticIndex = null;
    let reusoExercisesState = null; // null=desconhecido, true=tem exercícios, false=sem exercícios

    const session_id = window.session_id;
    const token = window.token;
    const domain_id = window.domain_id;
    const my_username = window.my_username;
    const my_id = window.my_id;


    // Verificar se o susuatio tem notas extras, se não tiver, exibir mensagem
    let student_extra_note = document.getElementById("student-extra-note-card-created");
    if (!student_extra_note) {
        document.getElementById("student-extra-note-card").innerHTML = '<em>Sem notas extras atribuidas.</em>';
    }

    // Verificar se o usuário é estudante e se não tem respostas de exercícios, exibir mensagem
    let student_answers_card = document.getElementById("student-answers-card-created");
    console.log("student_answers_card_created: ", student_answers_card);
    if (!student_answers_card) {
        console.log("student_answers_card>>: ", document.getElementById("student-answers-card"));
        document.getElementById("student-answers-card").innerHTML = '<em>Sem respostas de exercícios enviadas nesta sessão.</em>';
    }

    // Variável para armazenar a instância atual da UI do Chat
    let currentChatUI = null;

    console.log("Session ID: ", session_id);

    taticDescription("Sessão finalizada ou sem tática ativa no momento.");
    function taticDescription(description) {
        if (description === 'hidden' || description === undefined || description.trim() === "") {
            description = "Nenhuma descrição disponível";
        }
        const descriptionElement = document.getElementById("current_tatic_description");
        if (descriptionElement) descriptionElement.innerText = description;
    }


    function qual_tatica_esta_ativa(debate_sicrono, apresentacao_sincrona, reuso, envio_informacao, regras) {
        debateSicrono_isActive = debate_sicrono;
        apresentacaoSicrona_isActive = apresentacao_sincrona;
        reuso_isActive = reuso;
        envio_informacao_isActive = envio_informacao;
        regras_isActive = regras;
        // console.log("Tática Ativa: ", debateSicrono, apresentacaoSicrona, reuso);
    }


    function debateSicrono(id_chat, targetContainerId = "tatic_here") {
        fetch(`/chat_fragment/${id_chat}/${session_id}`)
            .then(response => response.text())
            .then(html => {
                const chatHere = document.createElement("div");
                chatHere.innerHTML = html;
                chatHere.id = "debate_sicrono";

                // Reexecutar scripts
                const scripts = Array.from(chatHere.querySelectorAll("script"));
                let loadedScripts = 0;
                const totalScripts = scripts.filter(s => s.src).length;

                scripts.forEach(oldScript => {
                    const newScript = document.createElement("script");

                    if (oldScript.src) {
                        newScript.src = oldScript.src;
                        newScript.onload = () => {
                            loadedScripts++;
                            if (loadedScripts === totalScripts && typeof initializeChatComponent === "function") {
                                if (currentChatUI) currentChatUI.destroy();
                                currentChatUI = initializeChatComponent();
                            }
                        };
                        document.body.appendChild(newScript);
                    } else {
                        newScript.textContent = oldScript.textContent;
                        document.body.appendChild(newScript);
                    }
                });

                if (totalScripts === 0 && typeof initializeChatComponent === "function") {
                    if (currentChatUI) currentChatUI.destroy();
                    currentChatUI = initializeChatComponent();
                }

                const chatContainer = document.getElementById(targetContainerId);
                chatContainer.innerHTML = "";
                chatContainer.appendChild(chatHere);
            });
    }


    function showAdaptiveReasoning(reasoning) {
        const banner = document.getElementById("adaptive-reasoning-banner");
        const text = document.getElementById("adaptive-reasoning-text");
        if (banner && text && reasoning) {
            text.textContent = reasoning;
            banner.classList.remove("d-none");
        }
    }

    function hideAdaptiveReasoning() {
        const banner = document.getElementById("adaptive-reasoning-banner");
        if (banner) banner.classList.add("d-none");
    }

    function showAdaptiveLoadingState() {
        clearInterval(countdownInterval);
        const timerEl = document.getElementById("tacticTimer");
        if (timerEl) timerEl.innerText = "...";
        const nameEl = document.getElementById("tacticName");
        if (nameEl) nameEl.innerText = "Personalizando...";
        const tacticArea = document.getElementById("tatic_here");
        if (tacticArea) {
            tacticArea.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" style="width:3rem;height:3rem;" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                    <p class="mt-3 fw-bold text-primary">🧠 A IA está personalizando seu ensino...</p>
                    <p class="text-muted small">Analisando seu perfil e desempenho para escolher a melhor próxima atividade.</p>
                </div>`;
        }
        hideAdaptiveReasoning();
    }

    function randomDelay(maxMs) {
        return new Promise(resolve => setTimeout(resolve, Math.random() * maxMs));
    }

    function advanceStudentTactic() {
        if (adaptiveTacticEnabled) {
            showAdaptiveLoadingState();
            return randomDelay(3000)
            .then(() => fetch('/orchestrator/agent/adaptive_next_tactic', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ student_id: my_id, session_id: session_id })
            }))
            .then(r => r.json())
            .then(aiData => {
                if (aiData.reasoning) {
                    localStorage.setItem(`adaptive_reasoning_${session_id}_${my_id}`, aiData.reasoning);
                }
                activeTacticIndex = null;
                fetchCurrentTactic(session_id);
            })
            .catch(() => { activeTacticIndex = null; fetchCurrentTactic(session_id); });
        } else {
            return fetch(`/sessions/${session_id}/student_advance_tactic`, { method: 'POST' })
                .then(() => { activeTacticIndex = null; fetchCurrentTactic(session_id); })
                .catch(() => fetchCurrentTactic(session_id));
        }
    }

    function startCountdown(remainingTime, strategyTactics, tacticName) {
        clearInterval(countdownInterval);
        // Limpa qualquer estado de loading (spinner da IA) antes de montar a nova tática
        const tacticHereEl = document.getElementById("tatic_here");
        if (tacticHereEl) tacticHereEl.innerHTML = '';

        // Reuso: se o tempo já expirou ao recarregar a página, garante pelo menos
        // 1 tick no branch "else" para que a UI de abas seja construída antes de parar.
        let timeLeft = (remainingTime <= 0 && tacticName === "Reuso") ? 1 : remainingTime;

        // Resetar estado de ativação a cada nova tática
        taticaAtiva = false;

        debateSicrono_isActive = false;
        apresentacaoSicrona_isActive = false;
        reuso_isActive = false;
        envio_informacao_isActive = false;
        regras_isActive = false;
        reusoExercisesState = null;

        // Remove os elementos da tática anterior antes de montar a nova
        removerElemento();

        countdownInterval = setInterval(() => {
            // Evitar auto-avanço se for a tática de "Regra", pois ela tem lógica própria de execução
            const isRegra = (tacticName === "Regra" || tacticName === "Regras");

            if (timeLeft <= 0 && !isRegra) {
                clearInterval(countdownInterval);
                const timerEl = document.getElementById("tacticTimer");
                if (timerEl) timerEl.innerText = "Concluído";

                const isReuso = (tacticName === "Reuso");
                if (isReuso && (reusoExercisesState === null || reusoExercisesState === true)) {
                    // Reuso com exercícios: aguarda o aluno completar e passar nos exercícios
                    return;
                }

                // Avança automaticamente para a próxima tática
                advanceStudentTactic();
            } else {
                let minutes = Math.floor(timeLeft / 60);
                let seconds = timeLeft % 60;
                let formattedTime = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                const timerEl2 = document.getElementById("tacticTimer");
                if (timerEl2) timerEl2.innerText = formattedTime;

                timeLeft--;

                // const elementToRemove = document.getElementById('chat');
                // if (elementToRemove) {
                //     elementToRemove.remove(); // Remove o próprio elemento
                // }

                // Verifica se a tática atual é "Debate Sincrono"
                if (tacticName == "Debate Sincrono") {

                    // Evitar adicionar o botão várias vezes:
                    if (!document.getElementById("debate_sicrono")) {

                        // (debate_sicrono, apresentacao_sincrona, reuso, envio_informacao, regras)
                        qual_tatica_esta_ativa(true, false, false, false, false);

                        removerElemento();

                        id_chat = null;
                        for (let tatic_stra in strategyTactics) {
                            // console.log(strategyTactics[tatic_stra].name);
                            if (strategyTactics[tatic_stra].name == "Debate Sincrono") {
                                id_chat = strategyTactics[tatic_stra].chat_id;
                                break;
                            }
                        }

                        if (taticaAtiva == false) {
                            console.log("Entrando no debate sincrono");
                            debateSicrono(id_chat);
                            taticaAtiva = true;
                        }
                    }
                }
                else if (tacticName == "Apresentacao Sincrona") {
                    if (!document.getElementById("apresentacao_sincrona")) {

                        // (debate_sicrono, apresentacao_sincrona, reuso, envio_informacao, regras)
                        qual_tatica_esta_ativa(false, true, false, false, false);
                        removerElemento();

                        let button = document.createElement("button");
                        button.innerHTML = `
            <span style="font-size: 1.5rem; font-weight: bold;">
                🎥 Entrar na Apresentação Síncrona
            </span>
        `;
                        button.id = "apresentacao_sincrona";

                        // Adicionando múltiplas classes do Bootstrap para destaque visual
                        button.className = "btn btn-warning shadow-lg border-3 border-dark mt-4 py-4 px-5 fs-4 rounded-pill";

                        link_do_meet = null;

                        for (let tatic_stra in strategyTactics) {
                            if (strategyTactics[tatic_stra].name == "Apresentacao Sincrona") {
                                link_do_meet = strategyTactics[tatic_stra].description;
                                break;
                            }
                        }

                        button.onclick = function () {
                            window.open(link_do_meet, "_blank");
                        };

                        let tatic_here = document.getElementById("tatic_here");
                        tatic_here.appendChild(button);
                    }
                }

                else if (tacticName == "Reuso") {
                    if (!document.getElementById("reuso_tabs")) {

                        qual_tatica_esta_ativa(false, false, true, false, false);
                        removerElemento();

                        const tatic_here = document.getElementById("tatic_here");

                        // Criar container das abas
                        const tabContainer = document.createElement("div");
                        tabContainer.id = "reuso_tabs";

                        tabContainer.innerHTML = `
            <ul class="nav nav-tabs" id="reusoTab" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="pdf-tab" data-bs-toggle="tab" data-bs-target="#pdfs" type="button" role="tab">PDFs</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="ex-tab" data-bs-toggle="tab" data-bs-target="#exercicios" type="button" role="tab">Exercícios</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="vid-tab" data-bs-toggle="tab" data-bs-target="#videos" type="button" role="tab">Vídeos</button>
                </li>
            </ul>
            <div class="tab-content mt-3">
                <div class="tab-pane fade show active" id="pdfs" role="tabpanel">
                    <div id="pdf_container"></div>
                </div>
                <div class="tab-pane fade" id="exercicios" role="tabpanel">
                    <div id="exercise_container" class="p-2">Carregando exercícios...</div>
                </div>
                <div class="tab-pane fade" id="videos" role="tabpanel">
                    <div id="video_container" class="p-2">Carregando vídeos...</div>
                </div>
            </div>
        `;


                        // Forçar o funcionamento das abas Bootstrap depois de adicionar dinamicamente
                        const tabTriggerList = tabContainer.querySelectorAll('button[data-bs-toggle="tab"]');
                        tabTriggerList.forEach(function (tabEl) {
                            tabEl.addEventListener('click', function (event) {
                                const tab = new bootstrap.Tab(tabEl);
                                tab.show();
                            });
                        });


                        tatic_here.appendChild(tabContainer);

                        // ---------- Carregar PDFs ----------
                        const pdfData = document.getElementById("pdf_data").getAttribute("data-pdfs");
                        const pdfs = JSON.parse(pdfData);

                        const pdfContainer = document.getElementById("pdf_container");
                        const _studyTextKey = `reuso_study_text_${session_id}_${my_id}`;
                        const _savedStudyText = localStorage.getItem(_studyTextKey);

                        if (_savedStudyText) {
                            // Restaura o texto gerado pela IA em tentativa anterior
                            const _card = document.createElement('div');
                            _card.className = 'card border-warning shadow-sm mb-3';
                            const _cardHeader = document.createElement('div');
                            _cardHeader.className = 'card-header bg-warning text-dark fw-bold';
                            _cardHeader.textContent = 'Material de Revisão Personalizado';
                            const _cardBody = document.createElement('div');
                            _cardBody.className = 'card-body';
                            const _hint = document.createElement('p');
                            _hint.className = 'text-muted small mb-3';
                            _hint.textContent = 'Leia este material antes de tentar novamente.';
                            const _textDiv = document.createElement('div');
                            _textDiv.style.cssText = 'white-space: pre-wrap; line-height: 1.8;';
                            _textDiv.textContent = _savedStudyText;
                            _cardBody.appendChild(_hint);
                            _cardBody.appendChild(_textDiv);
                            _card.appendChild(_cardHeader);
                            _card.appendChild(_cardBody);
                            pdfContainer.innerHTML = '';
                            pdfContainer.appendChild(_card);
                        } else {
                            pdfs.forEach(pdf => {
                                fetch(`/pdfs/${pdf.id}`, {
                                    headers: {
                                        "Authorization": `Bearer ${token}`
                                    }
                                })
                                    .then(response => {
                                        if (!response.ok) {
                                            throw new Error("Erro ao baixar PDF");
                                        }
                                        return response.blob();
                                    })
                                    .then(blob => {
                                        const url = URL.createObjectURL(blob);
                                        const embed = document.createElement("embed");
                                        embed.src = url;
                                        embed.type = "application/pdf";
                                        embed.width = "100%";
                                        embed.height = "600px";
                                        embed.className = "mb-3";

                                        pdfContainer.appendChild(embed);
                                    })
                                    .catch(error => {
                                        console.error("Erro ao carregar PDF: ", error);
                                    });
                            });
                        }

                        // ----------Carregar Exercícios----------
                        fetch(`/domains/${domain_id}/exercises`, {
                            headers: {
                                "Authorization": `Bearer ${token}`
                            }
                        })
                            .then(res => res.json())
                            .then(data => {
                                reusoExercisesState = data.length > 0;
                                const container = document.getElementById("exercise_container");

                                if (data.length === 0) {
                                    container.innerHTML = "<p class='text-muted'>Nenhum exercício encontrado.</p>";
                                    return;
                                }

                                // Cria o formulário principal
                                const form = document.createElement("form");
                                form.id = "exerciseForm";

                                console.log("Exercícios carregados:", data);

                                // Para cada exercício, cria um bloco com as perguntas
                                data.forEach((ex, index) => {
                                    const div = document.createElement("div");
                                    div.className = "mb-3 border rounded p-2 bg-light";
                                    div.innerHTML = `
                <p><strong>${index + 1}) ${ex.question}</strong></p>
                ${ex.options.map((opt, i) => `
                    <div>
                        <input type="radio" name="exercise_${ex.id}" value="${i}" required>
                        ${i + 1}) ${opt}
                    </div>
                `).join("")}
            `;
                                    form.appendChild(div);
                                });

                                // Botão de envio e feedback
                                form.innerHTML += `
            <button type="submit" class="btn btn-primary mt-3">Enviar respostas</button>
            <div id="formFeedback" class="mt-2 text-danger"></div>
        `;

                                container.innerHTML = ""; // Limpa qualquer conteúdo anterior
                                container.appendChild(form); // Insere o formulário

                                // Restaura countdown do botão se ainda estiver ativo após reload
                                const _cooldownKey = `reuso_cooldown_end_${session_id}_${my_id}`;
                                const _cooldownEnd = parseInt(localStorage.getItem(_cooldownKey) || '0');
                                if (_cooldownEnd > Date.now()) {
                                    const _restoreBtn = form.querySelector('button[type="submit"]');
                                    if (_restoreBtn) {
                                        _restoreBtn.disabled = true;
                                        let _secsLeft = Math.ceil((_cooldownEnd - Date.now()) / 1000);
                                        const _updateRestoreBtn = () => {
                                            const m = Math.floor(_secsLeft / 60);
                                            const s = _secsLeft % 60;
                                            _restoreBtn.textContent = `Aguarde ${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')} para tentar novamente`;
                                        };
                                        _updateRestoreBtn();
                                        const _restoreTimer = setInterval(() => {
                                            _secsLeft--;
                                            if (_secsLeft <= 0) {
                                                clearInterval(_restoreTimer);
                                                _restoreBtn.disabled = false;
                                                _restoreBtn.textContent = 'Enviar respostas';
                                                localStorage.removeItem(_cooldownKey);
                                            } else {
                                                _updateRestoreBtn();
                                            }
                                        }, 1000);
                                    }
                                }

                                // Adiciona o event listener de envio DEPOIS de inserir no DOM
                                form.addEventListener("submit", function (e) {
                                    e.preventDefault();

                                    const studentName = my_username;
                                    const studentId = my_id;

                                    if (!studentName || !studentId) {
                                        document.getElementById("formFeedback").textContent = "Preencha nome e ID do aluno.";
                                        return;
                                    }

                                    const formData = new FormData(e.target);
                                    const answers = [];

                                    for (const [key, value] of formData.entries()) {
                                        if (key.startsWith("exercise_")) {
                                            const exerciseId = key.split("_")[1];
                                            answers.push({
                                                exercise_id: parseInt(exerciseId),
                                                answer: parseInt(value)
                                            });
                                        }
                                    }

                                    const totalQuestions = data.length; // Cada objeto em `data` é uma pergunta
                                    if (answers.length !== totalQuestions) {
                                        document.getElementById("formFeedback").textContent = "Responda todas as questões antes de enviar.";
                                        return;
                                    }


                                    const submitBtn = form.querySelector('button[type="submit"]');
                                    if (submitBtn) submitBtn.disabled = true;

                                    fetch("/sessions/submit_answer", {
                                        method: "POST",
                                        headers: {
                                            "Content-Type": "application/json",
                                            "Authorization": `Bearer ${token}`
                                        },
                                        body: JSON.stringify({
                                            student_id: studentId,
                                            student_name: studentName,
                                            answers: answers,
                                            session_id: session_id,
                                        })
                                    })
                                        .then(function (response) {
                                            if (!response.ok) {
                                                throw new Error("Erro ao enviar respostas");
                                            }
                                            return response.json();
                                        })
                                        .then(function(respData) {
                                            const feedbackEl = document.getElementById("formFeedback");
                                            feedbackEl.textContent = respData.resp;
                                            console.log("Respostas enviadas:", respData);

                                            if (respData.passed) {
                                                feedbackEl.className = "mt-2 text-success fw-bold";
                                                // Limpa dados persistidos ao passar nos exercícios
                                                localStorage.removeItem(`reuso_cooldown_end_${session_id}_${my_id}`);
                                                localStorage.removeItem(`reuso_study_text_${session_id}_${my_id}`);
                                                if (adaptiveTacticEnabled) {
                                                    showAdaptiveLoadingState();
                                                    // activeTacticIndex é o índice da tática que o aluno ACABOU de concluir.
                                                    // Delay aleatório 0-3s para escalonar chamadas simultâneas.
                                                    const _completedIdx = activeTacticIndex;
                                                    randomDelay(3000)
                                                    .then(() => fetch('/orchestrator/agent/adaptive_next_tactic', {
                                                        method: 'POST',
                                                        headers: { 'Content-Type': 'application/json' },
                                                        body: JSON.stringify({ student_id: my_id, session_id: session_id, completed_tactic_index: _completedIdx })
                                                    }))
                                                    .then(r => r.json())
                                                    .then(aiData => {
                                                        if (aiData.reasoning) {
                                                            localStorage.setItem(`adaptive_reasoning_${session_id}_${my_id}`, aiData.reasoning);
                                                        }
                                                        activeTacticIndex = null;
                                                        setTimeout(() => fetchCurrentTactic(session_id), 500);
                                                    })
                                                    .catch(() => { activeTacticIndex = null; setTimeout(() => fetchCurrentTactic(session_id), 1500); });
                                                } else {
                                                    setTimeout(() => fetchCurrentTactic(session_id), 1500);
                                                }
                                            } else {
                                                feedbackEl.className = "mt-2 text-danger fw-bold";

                                                // --- Desabilita o botão por 3 minutos com countdown ---
                                                if (submitBtn) {
                                                    submitBtn.disabled = true;
                                                    const cooldownEndTime = Date.now() + 180 * 1000;
                                                    localStorage.setItem(`reuso_cooldown_end_${session_id}_${my_id}`, cooldownEndTime.toString());
                                                    let secondsLeft = 180;
                                                    const updateBtn = () => {
                                                        const mins = Math.floor(secondsLeft / 60);
                                                        const secs = secondsLeft % 60;
                                                        submitBtn.textContent = `Aguarde ${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')} para tentar novamente`;
                                                    };
                                                    updateBtn();
                                                    const btnCountdown = setInterval(() => {
                                                        secondsLeft--;
                                                        if (secondsLeft <= 0) {
                                                            clearInterval(btnCountdown);
                                                            submitBtn.disabled = false;
                                                            submitBtn.textContent = 'Enviar respostas';
                                                            localStorage.removeItem(`reuso_cooldown_end_${session_id}_${my_id}`);
                                                        } else {
                                                            updateBtn();
                                                        }
                                                    }, 1000);
                                                }

                                                // --- Modal informativo ---
                                                const existingModal = document.getElementById('wrongAnswersModal');
                                                if (existingModal) existingModal.remove();

                                                const modalEl = document.createElement('div');
                                                modalEl.id = 'wrongAnswersModal';
                                                modalEl.className = 'modal fade';
                                                modalEl.setAttribute('tabindex', '-1');
                                                modalEl.innerHTML = `
                                                    <div class="modal-dialog modal-dialog-centered">
                                                        <div class="modal-content border-warning">
                                                            <div class="modal-header bg-warning text-dark">
                                                                <h5 class="modal-title fw-bold">Resultado dos Exercícios</h5>
                                                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                                            </div>
                                                            <div class="modal-body">
                                                                <p class="fw-semibold">${feedbackEl.textContent}</p>
                                                                <hr>
                                                                <p id="modal-ai-status" class="mb-0">
                                                                    <span class="spinner-border spinner-border-sm text-warning me-2" role="status"></span>
                                                                    Gerando material de revisão personalizado com foco nos seus erros...
                                                                </p>
                                                            </div>
                                                            <div class="modal-footer">
                                                                <button type="button" class="btn btn-warning" data-bs-dismiss="modal">Fechar e Revisar</button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                `;
                                                document.body.appendChild(modalEl);
                                                const bsModal = new bootstrap.Modal(modalEl);
                                                bsModal.show();

                                                // --- Spinner na aba PDF ---
                                                const pdfContainer = document.getElementById("pdf_container");
                                                if (pdfContainer) {
                                                    pdfContainer.innerHTML = `
                                                        <div class="text-center p-4">
                                                            <div class="spinner-border text-warning" role="status"></div>
                                                            <p class="mt-2 text-muted">Gerando material de revisão personalizado...</p>
                                                        </div>
                                                    `;
                                                    const pdfTabBtn = document.getElementById("pdf-tab");
                                                    if (pdfTabBtn) new bootstrap.Tab(pdfTabBtn).show();
                                                }

                                                fetch('/orchestrator/agent/generate_wrong_answers_text', {
                                                    method: 'POST',
                                                    headers: { 'Content-Type': 'application/json' },
                                                    body: JSON.stringify({ student_id: studentId, session_id: session_id })
                                                })
                                                .then(r => r.json())
                                                .then(aiData => {
                                                    // Persiste o texto gerado para sobreviver a reloads
                                                    if (aiData.study_text) {
                                                        localStorage.setItem(`reuso_study_text_${session_id}_${my_id}`, aiData.study_text);
                                                    }

                                                    // Atualiza o modal com confirmação
                                                    const modalStatus = document.getElementById('modal-ai-status');
                                                    if (modalStatus) {
                                                        modalStatus.innerHTML = `
                                                            <span class="text-success fw-bold">Material gerado com sucesso!</span>
                                                            Acesse a aba <strong>PDFs</strong> para ler o conteúdo personalizado focado nas suas dificuldades.
                                                        `;
                                                    }

                                                    if (pdfContainer) {
                                                        const card = document.createElement('div');
                                                        card.className = 'card border-warning shadow-sm mb-3';

                                                        const cardHeader = document.createElement('div');
                                                        cardHeader.className = 'card-header bg-warning text-dark fw-bold';
                                                        cardHeader.textContent = 'Material de Revisão Personalizado';

                                                        const cardBody = document.createElement('div');
                                                        cardBody.className = 'card-body';

                                                        const hint = document.createElement('p');
                                                        hint.className = 'text-muted small mb-3';
                                                        hint.textContent = 'Leia este material antes de tentar novamente.';

                                                        const textDiv = document.createElement('div');
                                                        textDiv.style.cssText = 'white-space: pre-wrap; line-height: 1.8;';
                                                        textDiv.textContent = aiData.study_text || 'Não foi possível gerar o material. Tente novamente.';

                                                        cardBody.appendChild(hint);
                                                        cardBody.appendChild(textDiv);
                                                        card.appendChild(cardHeader);
                                                        card.appendChild(cardBody);
                                                        pdfContainer.innerHTML = '';
                                                        pdfContainer.appendChild(card);
                                                    }
                                                    form.reset();
                                                })
                                                .catch(() => {
                                                    const modalStatus = document.getElementById('modal-ai-status');
                                                    if (modalStatus) {
                                                        modalStatus.textContent = 'Não foi possível gerar o material automaticamente. Revise o conteúdo e tente novamente.';
                                                    }
                                                    form.reset();
                                                });
                                            }
                                        })
                                        .catch(function(err) {
                                            console.error("Erro ao enviar respostas:", err);
                                            const feedbackEl = document.getElementById("formFeedback");
                                            feedbackEl.textContent = "Erro ao enviar respostas. Tente novamente.";
                                            feedbackEl.className = "mt-2 text-danger";
                                            if (submitBtn) submitBtn.disabled = false;
                                        });
                                });
                            })
                            .catch(err => {
                                console.error("Erro ao carregar exercícios:", err);
                                reusoExercisesState = false;
                            });


                        // ---------- Carregar Vídeos ----------
                        fetch(`/domains/${domain_id}/videos`, {
                            headers: {
                                "Authorization": `Bearer ${token}`
                            }
                        })
                            .then(res => res.json())
                            // .then(res => console.log(res))
                            .then(videos_json => {
                                const container = document.getElementById("video_container");
                                container.innerHTML = "";

                                // console.log("videos_json: ", videos_json)

                                videos_json.videos_youtube.forEach(video => {
                                    const embedUrl = convertToEmbedUrl(video.url);
                                    const div = document.createElement("div");
                                    div.className = "mb-3";
                                    div.innerHTML = `<iframe width="560" height="315" 
                                        src="${embedUrl}" 
                                        title="YouTube video player" 
                                        frameborder="0" 
                                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                                        allowfullscreen></iframe>`;
                                    container.appendChild(div);
                                });

                                videos_json.videos_uploaded.forEach(video => {
                                    const videoTag = document.createElement("video");
                                    const div = document.createElement("div");
                                    videoTag.controls = true;
                                    videoTag.src = `/video/uploaded/${video.id}`;
                                    videoTag.className = "w-100";
                                    div.appendChild(videoTag);
                                    container.appendChild(div);
                                });
                            })
                            .catch(err => {
                                console.error("Erro ao carregar vídeos:", err);
                            });

                    }
                }


                else if (tacticName == "Envio de Informacao") {
                    if (!document.getElementById("envio_informacao_aviso")) {

                        // (debate_sicrono, apresentacao_sincrona, reuso, envio_informacao, regras)
                        qual_tatica_esta_ativa(false, false, false, true, false);
                        removerElemento();

                        // Criar container visual com mensagem e botão
                        const avisoDiv = document.createElement("div");
                        avisoDiv.id = "envio_informacao_aviso";
                        avisoDiv.className = "alert alert-info shadow-lg p-4 rounded border border-primary";

                        avisoDiv.innerHTML = `
            <h4 class="mb-3 text-primary">
                📬 Verifique seu e-mail!
            </h4>
            <p class="lead mb-4">
                Acabamos de enviar um material importante para o e-mail cadastrado.
                Por favor, confira sua caixa de entrada!
            </p>
            <button class="btn btn-success btn-lg px-4 py-2 rounded-pill fw-bold" id="btn_ver_email_gmail">
                Ir para o Gmail ✉️
            </button>
            <button class="btn btn-success btn-lg px-4 py-2 rounded-pill fw-bold" id="btn_ver_email_outlook">
                Ir para o Outlook ✉️
            </button>
        `;

                        // Adicionar ação ao botão
                        avisoDiv.querySelector("#btn_ver_email_gmail").onclick = function () {
                            window.open("https://mail.google.com/", "_blank");
                        };

                        avisoDiv.querySelector("#btn_ver_email_outlook").onclick = function () {
                            window.open("https://outlook.live.com/", "_blank");
                        };

                        let tatic_here = document.getElementById("tatic_here");
                        tatic_here.appendChild(avisoDiv);
                    }
                }

                // --------------------------------------------------------
                // NOVA LÓGICA: TÁTICA DE REGRA (Agente Decisor)
                // --------------------------------------------------------
                else if (tacticName == "Regra" || tacticName == "Regras") {
                    // Evita executar múltiplas vezes se já estiver "ativo" ou processando
                    if (!document.getElementById("regra_processing")) {

                        // (debate_sicrono, apresentacao_sincrona, reuso, envio_informacao, regras)
                        qual_tatica_esta_ativa(false, false, false, false, true);
                        removerElemento();

                        const tatic_here = document.getElementById("tatic_here");

                        // Card visual de processamento
                        const processingDiv = document.createElement("div");
                        processingDiv.id = "regra_processing";
                        processingDiv.className = "card shadow border-primary mb-3 text-center p-4";
                        processingDiv.innerHTML = `
                            <div class="card-body">
                                <h3 class="card-title text-primary mb-3">
                                    <i class="bi bi-cpu-fill"></i> Agente de Estratégia
                                </h3>
                                <p class="card-text lead">
                                    Analisando o desempenho da turma e o conteúdo para decidir o próximo passo...
                                </p>
                                <div class="spinner-border text-primary mt-3" role="status" style="width: 3rem; height: 3rem;">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2 text-muted"><small>Isso pode levar alguns segundos.</small></p>
                            </div>
                        `;
                        tatic_here.appendChild(processingDiv);

                        // --- Chamada ao Backend ---
                        console.log("Iniciando execução da Tática de Regras...");
                        fetch(`/sessions/${session_id}/execute_rules`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ student_id: my_id })
                        })
                        .then(response => {
                            if (!response.ok) throw new Error("Erro na execução da regra");
                            return response.json();
                        })
                        .then(data => {
                            console.log("Decisão do Agente de Regras:", data);

                            // Atualiza a UI com a decisão
                            processingDiv.innerHTML = `
                                <div class="card-body">
                                    <h3 class="card-title text-success mb-3">
                                        <i class="bi bi-check-circle-fill"></i> Decisão Tomada!
                                    </h3>
                                    <p class="card-text lead">
                                        <strong>Ação:</strong> ${data.decision === 'REPEAT_TACTIC' ? 'Reforço de Conteúdo (Repetir Tática)' : 'Avançar Estratégia'}
                                    </p>
                                    <div class="alert alert-secondary text-start" role="alert">
                                        <strong><i class="bi bi-lightbulb"></i> Motivo:</strong> ${data.reasoning}
                                    </div>
                                    <p class="mt-3 text-muted">Redirecionando...</p>
                                </div>
                            `;

                            // Pequeno delay para leitura antes de recarregar
                            setTimeout(() => {
                                location.reload();
                            }, 4000);
                        })
                        .catch(err => {
                            console.error("Falha na regra:", err);
                            processingDiv.innerHTML = `
                                <div class="alert alert-danger">
                                    Ocorreu um erro ao processar a regra. Avançando automaticamente...
                                </div>
                            `;
                            // Fallback: Avança forçado após erro
                            setTimeout(() => {
                                fetch(`/sessions/${session_id}/next_tactic`, { method: 'POST' })
                                .then(() => location.reload());
                            }, 3000);
                        });
                    }
                }
            }

        }, 1000);
    }

    function convertToEmbedUrl(url) {
        try {
            const parsedUrl = new URL(url);
            const videoId = parsedUrl.searchParams.get("v");
            if (videoId) {
                return `https://www.youtube.com/embed/${videoId}`;
            }
            return url; // fallback: se não tiver parâmetro "v"
        } catch (e) {
            console.error("URL inválida:", url);
            return url;
        }
    }


    function removerElemento() {
        let reusoTabs = document.getElementById("reuso_tabs");
        if (reusoTabs && !reuso_isActive) {
            reusoTabs.remove();
        }

        let apresentacao_sincrona = document.getElementById("apresentacao_sincrona");
        if (apresentacao_sincrona && !apresentacaoSicrona_isActive) {
            apresentacao_sincrona.remove();
        }

        let chatElement = document.getElementById("debate_sicrono");
        if (!debateSicrono_isActive) {
             if (chatElement) {
                 chatElement.remove();
             }

             // Limpeza correta da UI usando o método destroy() da classe
             if (currentChatUI) {
                 console.log("Limpando instância da UI do Chat...");
                 currentChatUI.destroy();
                 currentChatUI = null;
             }

             // O Service (socket) pode permanecer conectado ou ser desconectado aqui
             // Se quisermos desconectar totalmente ao sair da aba:
             // if (window.ChatService && window.ChatService.instance) {
             //    window.ChatService.instance.disconnect();
             // }
        }

        let envio_informacao_aviso = document.getElementById("envio_informacao_aviso");
        if (envio_informacao_aviso && !envio_informacao_isActive) {
            envio_informacao_aviso.remove();
        }

        let regraProcessing = document.getElementById("regra_processing");
        if (regraProcessing && !regras_isActive) {
            regraProcessing.remove();
        }
    }

    function realod_page() {
        console.log("Recarregando a página...");
        location.reload();
    }

    function showStudentStartArea() {
        const startArea = document.getElementById("student-start-area");
        const tacticArea = document.getElementById("student-tactic-area");
        if (startArea) startArea.style.display = '';
        if (tacticArea) tacticArea.style.display = 'none';
    }

    function showStudentTacticArea() {
        const startArea = document.getElementById("student-start-area");
        const tacticArea = document.getElementById("student-tactic-area");
        if (startArea) startArea.style.display = 'none';
        if (tacticArea) tacticArea.style.display = '';
    }

    function fetchCurrentTactic(session_id) {
        const studentParam = my_id ? `?student_id=${my_id}` : '';
        fetch(`/sessions/${session_id}/current_tactic${studentParam}`)
            .then(response => response.json())
            .then(data => {
                console.log("Dados da tática atual: ", data);

                adaptiveTacticEnabled = data.adaptive_tactic_enabled || false;

                if (data.strategy_id && window.current_strategy_id && data.strategy_id != window.current_strategy_id) {
                    console.log("Strategy changed, reloading page...");
                    location.reload();
                    return;
                }

                if (data.session_status === 'not_started') {
                    // Sessão iniciada/reiniciada pelo professor: limpa material e timer do Reuso
                    localStorage.removeItem(`reuso_study_text_${session_id}_${my_id}`);
                    localStorage.removeItem(`reuso_cooldown_end_${session_id}_${my_id}`);
                    localStorage.removeItem(`adaptive_reasoning_${session_id}_${my_id}`);
                    hideAdaptiveReasoning();
                    activeTacticIndex = null;
                    showStudentStartArea();
                    const btn = document.getElementById("studentStartBtn");
                    if (btn) {
                        btn.disabled = false;
                        btn.innerHTML = '<i class="bi bi-play-circle-fill me-2"></i> Iniciar Minha Sessão';
                    }
                    const msg = document.getElementById("student-start-msg");
                    if (msg) msg.innerText = "Clique para iniciar o seu percurso de aprendizagem.";
                    return;
                }

                if (data.session_status === 'aguardando') {
                    showStudentStartArea();
                    const btn = document.getElementById("studentStartBtn");
                    if (btn) {
                        btn.disabled = true;
                        btn.innerHTML = '<i class="bi bi-hourglass me-2"></i> Aguardando professor abrir a sessão…';
                    }
                    return;
                }

                if (data.tactic && data.session_status === 'in-progress') {
                    showStudentTacticArea();
                    const nameEl = document.getElementById("tacticName");
                    if (nameEl) nameEl.innerText = data.tactic.name;
                    taticDescription(data.tactic.description || "Nenhuma descrição disponível");
                    if (data.current_tactic_index !== activeTacticIndex) {
                        activeTacticIndex = data.current_tactic_index;

                        // Exibe o raciocínio da IA se existir no localStorage
                        if (adaptiveTacticEnabled) {
                            const storedReasoning = localStorage.getItem(`adaptive_reasoning_${session_id}_${my_id}`);
                            if (storedReasoning) {
                                showAdaptiveReasoning(storedReasoning);
                                localStorage.removeItem(`adaptive_reasoning_${session_id}_${my_id}`);
                            } else {
                                hideAdaptiveReasoning();
                            }
                        } else {
                            hideAdaptiveReasoning();
                        }

                        const tacticNameLower = data.tactic.name.trim().toLowerCase();
                        const isMudancaEstrategia =
                            tacticNameLower.includes('mudança de estratégia') ||
                            tacticNameLower.includes('mudanca de estrategia') ||
                            tacticNameLower.includes('mudança de estrategia') ||
                            tacticNameLower.includes('mudanca de estratégia');

                        if (isMudancaEstrategia) {
                            clearInterval(countdownInterval);
                            const timerEl = document.getElementById("tacticTimer");
                            if (timerEl) timerEl.innerText = "...";
                            taticDescription("Mudando de estratégia, aguarde...");
                            const description = data.tactic.description || '';
                            const matchId = description.match(/\d+/);
                            if (matchId) {
                                const newStrategyId = parseInt(matchId[0]);
                                fetch(`/sessions/${session_id}/student_change_strategy`, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ strategy_id: newStrategyId })
                                })
                                .then(() => { activeTacticIndex = null; setTimeout(() => location.reload(), 1000); })
                                .catch(() => {
                                    activeTacticIndex = null;
                                    fetch(`/sessions/${session_id}/student_advance_tactic`, { method: 'POST' })
                                        .then(() => fetchCurrentTactic(session_id))
                                        .catch(() => fetchCurrentTactic(session_id));
                                });
                            } else {
                                activeTacticIndex = null;
                                fetch(`/sessions/${session_id}/student_advance_tactic`, { method: 'POST' })
                                    .then(() => fetchCurrentTactic(session_id))
                                    .catch(() => fetchCurrentTactic(session_id));
                            }
                        } else {
                            startCountdown(data.remaining_time, data.strategy_tactics, data.tactic.name);
                        }
                    }
                } else if (data.session_status === 'student_finished') {
                    activeTacticIndex = null;
                    clearInterval(countdownInterval);
                    qual_tatica_esta_ativa(false, false, false, false, false);
                    removerElemento();
                    showStudentStartArea();
                    const btn = document.getElementById("studentStartBtn");
                    if (btn) {
                        btn.disabled = true;
                        btn.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i> Sessão concluída! Aguardando o professor reiniciar...';
                    }
                    const msg = document.getElementById("student-start-msg");
                    if (msg) msg.innerText = "Parabéns! Você completou todas as táticas. O professor poderá reiniciar a sessão.";
                } else {
                    activeTacticIndex = null;
                    const nameEl = document.getElementById("tacticName");
                    const timerEl = document.getElementById("tacticTimer");
                    if (nameEl) nameEl.innerText = "Sessão finalizada";
                    if (timerEl) timerEl.innerText = "--";
                    qual_tatica_esta_ativa(false, false, false, false, false);
                    removerElemento();
                    taticDescription("Sessão finalizada ou sem tática ativa no momento.");
                    clearInterval(countdownInterval);
                }
            })
            .catch(error => {
                console.error("Erro ao buscar tática atual:", error.message);
                const nameEl = document.getElementById("tacticName");
                const timerEl = document.getElementById("tacticTimer");
                if (nameEl) nameEl.innerText = "Erro ao carregar";
                if (timerEl) timerEl.innerText = "--";
            });
    }


    // ===== PROFESSOR =====
    const startSessionBtn = document.getElementById("startSessionBtn");
    if (startSessionBtn) {
        startSessionBtn.addEventListener("click", () => {
            fetch(`/sessions/start/${session_id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ use_agent: false })
            }).then(response => {
                if (response.ok) {
                    location.reload();
                } else {
                    alert("Sessão já iniciada ou erro ao iniciar.");
                }
            });
        });
    }

    const endSessionBtn = document.getElementById("endSessionBtn");
    if (endSessionBtn) {
        endSessionBtn.addEventListener("click", () => {
            if (confirm("Tem certeza que deseja encerrar a sessão?")) {
                fetch(`/sessions/end/${session_id}`)
                    .then(response => {
                        if (response.ok) {
                            location.reload();
                        } else {
                            alert("Erro ao encerrar a sessão.");
                        }
                    })
                    .catch(() => alert("Erro ao tentar encerrar a sessão."));
            }
        });
    }

    if (window.user_type === 'teacher') {
        if (window.teacher_debate_chat_id !== null && window.teacher_debate_chat_id !== undefined) {
            const debateSection = document.getElementById("teacher-debate-section");
            if (debateSection) debateSection.classList.remove("d-none");
            debateSicrono(window.teacher_debate_chat_id, "teacher_debate_chat");
        }
        if (window.teacher_apresentacao_link) {
            const apresentacaoSection = document.getElementById("teacher-apresentacao-section");
            if (apresentacaoSection) apresentacaoSection.classList.remove("d-none");
        }
    }

    // ===== ALUNO =====
    const studentStartBtn = document.getElementById("studentStartBtn");
    if (studentStartBtn) {
        studentStartBtn.addEventListener("click", () => {
            studentStartBtn.disabled = true;
            fetch(`/sessions/${session_id}/student_start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            }).then(response => {
                if (response.ok) {
                    showStudentTacticArea();
                    if (adaptiveTacticEnabled) {
                        // IA escolhe qual tática iniciar (mesmo a primeira).
                        // Delay aleatório 0-3s para escalonar chamadas de múltiplos alunos simultâneos.
                        showAdaptiveLoadingState();
                        randomDelay(3000)
                        .then(() => fetch('/orchestrator/agent/adaptive_next_tactic', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ student_id: my_id, session_id: session_id, is_first: true })
                        }))
                        .then(r => r.json())
                        .then(aiData => {
                            if (aiData.reasoning) {
                                localStorage.setItem(`adaptive_reasoning_${session_id}_${my_id}`, aiData.reasoning);
                            }
                            activeTacticIndex = null;
                            fetchCurrentTactic(session_id);
                        })
                        .catch(() => { activeTacticIndex = null; fetchCurrentTactic(session_id); });
                    } else {
                        fetchCurrentTactic(session_id);
                    }
                } else {
                    studentStartBtn.disabled = false;
                    alert("Erro ao iniciar a sessão. Tente novamente.");
                }
            }).catch(() => {
                studentStartBtn.disabled = false;
                alert("Erro ao iniciar a sessão. Tente novamente.");
            });
        });
    }

    if (window.user_type === 'student') {
        fetchCurrentTactic(session_id);
        setInterval(() => fetchCurrentTactic(session_id), 5000);
    }

    const adaptiveTacticSwitch = document.getElementById("adaptiveTacticSwitch");
    if (adaptiveTacticSwitch) {
        adaptiveTacticSwitch.addEventListener("change", function () {
            const enabled = this.checked;
            fetch(`/sessions/${session_id}/set_adaptive_tactic`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: enabled })
            })
            .then(r => r.json())
            .then(() => {
                adaptiveTacticEnabled = enabled;
                const statusEl = document.getElementById("adaptive-tactic-status");
                if (statusEl) {
                    statusEl.textContent = enabled
                        ? "Ativado: a IA escolhe a próxima tática para cada aluno."
                        : "Desativado: alunos seguem a ordem normal das táticas.";
                }
            })
            .catch(err => console.error("Erro ao atualizar tática adaptativa:", err));
        });
    }
});
