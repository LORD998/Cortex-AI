<div align="center">
  <img src="https://img.shields.io/badge/Cortex-AI-8A2BE2?style=for-the-badge&logo=openai&logoColor=white" alt="Cortex AI Logo"/>
  <h1>Cortex AI - Assistente Virtual Inteligente</h1>
  <p>Uma assistente de voz nativa para Windows, inspirada na fluidez e design da Apple Intelligence (Siri), 100% local e construída em Python.</p>
</div>

---

## 🌟 O que é a Cortex AI?
A Cortex AI é uma inteligência artificial que vive no teu ambiente de trabalho do Windows de forma totalmente invisível e interativa. Com um simples toque no teclado, surge uma esfera flutuante de design "premium" com cores vibrantes, pronta para te ouvir, conversar e ajudar em qualquer tarefa!

Toda a lógica de conversação é processada localmente utilizando o poder do **Ollama** (Qwen3:8b), o que significa que é privada, segura e não depende da cloud.

## ✨ Funcionalidades Principais
- 🎙️ **Modo Walkie-Talkie:** Pressiona e segura a tecla `ALT` para falar com a Cortex. Solta para ela te responder.
- 👩‍🏫 **Modo Professora / Conselheira:** Pede à Cortex para te ensinar inglês, francês, matemática ou dar conselhos vitais ("*Cortex, entra no modo professora de inglês*").
- 🔮 **Design Premium (Orb Holográfico):** Interface flutuante sem bordas (PyQt6), recriando a estética das inteligências artificiais topo de gama (Ciano, Rosa Choque e Violeta).
- 🧠 **Processamento Local:** Utiliza um servidor local Ollama, garantindo resposta rápida sem uso abusivo de Internet.
- 👻 **Modo Invisível (Background):** Funciona sem terminais abertos ou ícones chatos na barra de tarefas. Pode arrancar automaticamente com o Windows.

---

## 🛠️ Tecnologias Utilizadas
- **Python 3.x**
- **PyQt6** (Para a interface gráfica da Esfera Flutuante)
- **Keyboard** (Para hooks globais e atalhos)
- **Ollama** (Motor de inferência LLM Local)
- **SpeechRecognition** & **TTS** (Para ouvir e falar em tempo real)

---

## 🚀 Como Instalar e Usar

1. **Clonar o Repositório:**
   ```bash
   git clone https://github.com/LORD998/Cortex-AI.git
   cd Cortex-AI
   ```

2. **Instalar Dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Iniciar o Servidor Ollama:**
   Certifica-te que tens o [Ollama](https://ollama.com/) instalado no teu computador e que o modelo `qwen3:8b` está descarregado:
   ```bash
   ollama run qwen3:8b
   ```

4. **Ligar a Cortex:**
   Basta executar o script VBS escondido para a ligares sem abrir nenhuma janela preta:
   ```bash
   start_cortex_hidden.vbs
   ```
   *(Em alternativa podes correr o `cortex_overlay.py` diretamente).*

---

## 💡 Como Funciona
Assim que a Cortex estiver ligada, podes fechar tudo. Enquanto estiveres no Windows, **carrega no `ALT`**! Uma esfera brilhante aparecerá e vai ouvir a tua voz. Assim que soltares a tecla, ela processa e responde-te falando e escrevendo a resposta.

---

<div align="center">
  <i>Desenvolvido com 🧠 e muito código!</i>
</div>
