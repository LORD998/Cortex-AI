// index.js
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const pino = require('pino');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const { calculateTypingDelay, sleep, splitIntoHumanMessages } = require('./humanBehavior');

// Configura o logger do baileys (silent para não poluir o terminal)
const logger = pino({ level: 'silent' });

/**
 * Função para gerar resposta da Inteligência Artificial.
 * Se o Ollama estiver rodando localmente (ex: llama3), ele usará a IA real.
 * Caso contrário, usará respostas predefinidas como fallback.
 */
async function getLLMResponse(userMessage) {
    try {
        // Tenta se conectar a um LLM local rodando na porta 11434 (padrão Ollama)
        const res = await axios.post('http://127.0.0.1:11434/api/generate', {
            model: 'llama3', // Modelo padrão, você pode alterar para gemma, mistral, etc.
            prompt: `Você é um assistente de WhatsApp humano e natural. Responda em português de forma amigável à seguinte mensagem: ${userMessage}`,
            stream: false
        }, { timeout: 10000 });
        
        return res.data.response;
    } catch (e) {
        // Se a API não estiver rodando ou der erro, usamos as respostas naturais de fallback
        console.log("⚠️ LLM Local (Ollama) não detectado ou erro na API. Usando respostas de fallback.");
        const responses = [
            "Opa, tudo bem? ✌️ Entendi o que você quis dizer.",
            "Nossa, que interessante haha! Me conta mais.",
            "Anotado aqui! Vou dar uma olhada e já te retorno.\n\nEspera só um pouquinho.",
            "Humm, faz bastante sentido."
        ];
        return responses[Math.floor(Math.random() * responses.length)];
    }
}

async function connectToWhatsApp() {
    // Salva a sessão na pasta 'auth_info_baileys' para não pedir QR Code sempre
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys');
    
    const sock = makeWASocket({
        auth: state,
        printQRInTerminal: false,
        logger,
        browser: ["Watz Bot", "Chrome", "1.0.0"],
        syncFullHistory: false
    });

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr) {
            console.log("\n📲 Escaneie o QR Code abaixo para conectar seu WhatsApp (Bot de Alta Velocidade):\n");
            qrcode.generate(qr, { small: true });
        }
        
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect.error)?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('❌ Conexão fechada. Reconectando:', shouldReconnect);
            if (shouldReconnect) {
                connectToWhatsApp();
            }
        } else if (connection === 'open') {
            console.log('✅ Watz Bot conectado com sucesso! Pronto para responder com comportamento humano.');
        }
    });

    // Salva as credenciais sempre que forem atualizadas
    sock.ev.on('creds.update', saveCreds);

    // Escuta novas mensagens
    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;
        
        const m = messages[0];
        if (!m.message) return; // Ignora se não tiver corpo de mensagem
        if (m.key.fromMe) return; // Ignora as próprias mensagens

        const messageType = Object.keys(m.message)[0];
        
        // Pega o texto da mensagem
        let text = '';
        if (messageType === 'conversation') {
            text = m.message.conversation;
        } else if (messageType === 'extendedTextMessage') {
            text = m.message.extendedTextMessage.text;
        }
        
        if (text) {
            const senderId = m.key.remoteJid;
            console.log(`📩 Nova mensagem recebida: "${text}"`);

            // 1. Marca a mensagem como lida (Blue tick) - Comportamento Humano
            // Espera uns segundos antes de "ver" a mensagem
            await sleep(1500 + Math.random() * 2000);
            await sock.readMessages([m.key]);
            
            // 2. Processa a resposta da IA
            const aiResponse = await getLLMResponse(text);
            
            // 3. Divide a resposta em várias mensagens curtas (Comportamento Humano)
            const messagesToSend = splitIntoHumanMessages(aiResponse);
            
            for (let i = 0; i < messagesToSend.length; i++) {
                const chunk = messagesToSend[i];
                
                // Simula que está digitando
                await sock.sendPresenceUpdate('composing', senderId);
                
                // Calcula o atraso para simular o tempo de digitação daquela string
                const delay = calculateTypingDelay(chunk);
                console.log(`⏳ Simulando digitação por ${Math.round(delay/1000)}s...`);
                await sleep(delay);
                
                // Para de digitar
                await sock.sendPresenceUpdate('paused', senderId);
                
                // Envia a mensagem
                await sock.sendMessage(senderId, { text: chunk });
                
                // Pausa pequena entre o envio de múltiplas mensagens
                if (i < messagesToSend.length - 1) {
                    await sleep(1000 + Math.random() * 1500); 
                }
            }
        }
    });
}

// Inicia o bot
connectToWhatsApp();
