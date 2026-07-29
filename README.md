# Cortex AI

Assistente pessoal local para Windows, com cérebro Ollama, voz offline, visão,
memória e ferramentas reais para interagir com ficheiros, aplicações e serviços.

## O que já funciona

- Conversa local com `qwen3:8b` através do Ollama.
- Ciclo de agente multi-etapas: pensa, usa uma ferramenta, verifica o resultado
  e continua até concluir ou atingir o limite seguro.
- Roteamento contextual: o modelo recebe apenas as ferramentas relevantes para
  o pedido, em vez das 55 ferramentas ao mesmo tempo.
- Voz para texto offline com `faster-whisper`.
- Voz neural feminina brasileira `pf_dora` com Kokoro. Piper continua disponível
  como alternativa rápida e a voz SAPI do Windows fica como último recurso.
- Raciocínio automático: pedidos simples usam o modo rápido; análise,
  planeamento e tarefas complexas ativam pensamento aprofundado.
- Tradução de chamadas com deteção automática do idioma, tradução local pelo
  Ollama e saída configurável para outro idioma.
- Visão do ecrã com `qwen3-vl:8b`.
- Memória local em `memoria_cortex.json`.
- Gmail: listar, ler, preparar rascunhos, preparar respostas e enviar após
  confirmação explícita.
- Ferramentas de ficheiros, janelas, sistema, teclado, rato, pesquisa e dados.

## Privacidade real

O cérebro, o reconhecimento de voz, a tradução e a síntese de voz são locais.
Depois do primeiro download do modelo Whisper, estas funções não enviam áudio
para Google, Microsoft Edge TTS ou serviços de tradução.

Funções que naturalmente dependem da Internet — Gmail, pesquisa web, emprego,
Shopify e abertura de páginas — continuam a usar a Internet apenas quando forem
pedidas.

## Segurança

A Cortex pede confirmação antes de:

- enviar e-mail;
- apagar, mover, renomear, copiar ou sobrescrever ficheiros;
- executar comandos no terminal;
- instalar programas;
- fechar janelas;
- terminar processos, limpar temporários, reiniciar, suspender ou desligar.

Procurar duplicados apenas cria um relatório; já não apaga ficheiros. A extração
de ZIP também bloqueia caminhos que tentem escrever fora da pasta escolhida.

## Requisitos

- Windows 10 ou 11;
- Python 3.11 ou superior;
- Ollama;
- microfone;
- GPU recomendada, mas não obrigatória.

## Instalação

```powershell
python -m pip install -r requirements.txt
python scripts/setup_local_voice.py
ollama pull qwen3:8b
ollama pull qwen3-vl:8b
```

O script descarrega a voz portuguesa Piper e as vozes Kokoro. O
`faster-whisper` descarrega o modelo `small` na primeira utilização. Depois,
fica tudo guardado localmente. Na máquina atual, o Whisper já foi validado na RTX
e a voz é pré-carregada em segundo plano ao iniciar.

## Iniciar

```powershell
python cortex_overlay.py
```

Também podes usar `start_cortex_hidden.vbs` para iniciar sem uma consola visível.

- Mantém `ALT` premido para falar e solta para enviar.
- Pressiona `0` para ligar ou desligar o tradutor de chamada.
- Diz “modo professora de inglês” para iniciar uma aula.
- Diz “sair da aula” para voltar ao modo normal.

## Configuração

Copia `.env.example` para `.env` apenas se quiseres mudar os valores padrão:

```powershell
Copy-Item .env.example .env
```

Opções principais:

```dotenv
CORTEX_MODEL=qwen3:8b
CORTEX_CONTEXT_SIZE=8192
CORTEX_REASONING=auto
CORTEX_WHISPER_MODEL=small
CORTEX_WHISPER_DEVICE=auto
CORTEX_TTS_ENGINE=kokoro
CORTEX_TTS_VOICE_PT=pf_dora
CORTEX_TTS_SPEED=1.0
CORTEX_TRANSLATOR_TARGET=en
```

`CORTEX_REASONING=auto` dá prioridade à velocidade e ativa raciocínio profundo
quando deteta análise, planeamento ou vários passos. Usa `on` para o manter
sempre ativo ou `off` para máxima rapidez.

`CORTEX_TTS_SPEED` aceita valores de `0.75` a `1.25`. O padrão `1.0` preserva a
cadência natural da voz feminina. Para voltar à voz portuguesa masculina mais
rápida, usa `CORTEX_TTS_ENGINE=piper`.

Para melhorar o reconhecimento de vários idiomas, podes usar
`CORTEX_WHISPER_MODEL=medium`, com maior consumo de memória e tempo.

O idioma de saída do tradutor usa códigos como `en`, `de`, `es`, `fr`, `it`,
`ru`, `ja` ou `zh`. Para enviar a voz traduzida a Discord/Zoom, instala um cabo
de áudio virtual que apareça como `CABLE Input`.

## Gmail

O Gmail é opcional. Define o caminho do ficheiro OAuth autorizado:

```dotenv
CORTEX_GMAIL_CREDENTIALS=C:\caminho\seguro\gmail_credentials.json
```

A Cortex prefere criar rascunhos. O envio real continua bloqueado até dizeres
“confirmo”.

## Testes

```powershell
python -m unittest discover -s tests -v
python -m compileall -q core modules
```

Os testes que captam microfone ou chamam serviços reais foram movidos para
`scripts/manual_test_*.py`, para não ativarem hardware durante testes automáticos.

## Estrutura

```text
core/
  config.py          configuração central
  nlp_engine.py      cliente Ollama
  orchestrator.py    agente, ferramentas e confirmações
  tool_router.py     seleção contextual de ferramentas
modules/
  local_speech.py    Whisper, Piper, Kokoro e SAPI locais
  voice_manager.py   microfone e voz da assistente
  translator_manager.py
  email_manager.py
  ...
tests/
  test_core.py
```
