import SwiftUI
import AVFoundation

struct ChatView: View {
    @StateObject private var chatService = ChatService.shared
    @State private var inputText = ""
    @State private var showImagePicker = false
    @State private var selectedImage: UIImage?
    @State private var isShowingError = false
    @State private var errorMessage = ""
    @State private var isLoading = false
    
    var body: some View {
        VStack {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(chatService.messages) { message in
                            MessageView(message: message)
                                .id(message.id)
                        }
                    }
                    .padding()
                }
                .onChange(of: chatService.messages.count) { _ in
                    if let lastMessage = chatService.messages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }
            
            Divider()
            
            HStack(spacing: 8) {
                // 语音按钮
                Button(action: handleVoiceButton) {
                    Image(systemName: chatService.isRecording ? "stop.circle.fill" : "mic.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(chatService.isRecording ? .red : .blue)
                }
                .disabled(isLoading)
                
                // 图片按钮
                Button(action: { showImagePicker = true }) {
                    Image(systemName: "photo.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(.blue)
                }
                .disabled(isLoading || chatService.isRecording)
                
                // 文本输入框
                TextField("输入消息...", text: $inputText)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .disabled(chatService.isRecording)
                
                // 发送按钮
                Button(action: sendMessage) {
                    Image(systemName: "paperplane.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(.blue)
                }
                .disabled(inputText.isEmpty || isLoading || chatService.isRecording)
            }
            .padding()
        }
        .navigationTitle("聊天")
        .sheet(isPresented: $showImagePicker) {
            ImagePicker(image: $selectedImage)
        }
        .onChange(of: selectedImage) { newImage in
            if let image = newImage {
                Task {
                    await sendImage(image)
                }
            }
        }
        .alert("错误", isPresented: $isShowingError) {
            Button("确定", role: .cancel) {}
        } message: {
            Text(errorMessage)
        }
    }
    
    private func handleVoiceButton() {
        if chatService.isRecording {
            Task {
                await stopRecording()
            }
        } else {
            startRecording()
        }
    }
    
    private func startRecording() {
        do {
            try chatService.startRecording()
        } catch {
            isShowingError = true
            errorMessage = error.localizedDescription
        }
    }
    
    private func stopRecording() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            try await chatService.stopRecordingAndSend()
        } catch {
            isShowingError = true
            errorMessage = error.localizedDescription
        }
    }
    
    private func sendMessage() {
        guard !inputText.isEmpty else { return }
        
        let text = inputText
        inputText = ""
        
        Task {
            isLoading = true
            defer { isLoading = false }
            
            do {
                try await chatService.sendTextMessage(text)
            } catch {
                isShowingError = true
                errorMessage = error.localizedDescription
            }
        }
    }
    
    private func sendImage(_ image: UIImage) async {
        isLoading = true
        defer {
            isLoading = false
            selectedImage = nil
        }
        
        do {
            try await chatService.sendImageMessage(image)
        } catch {
            isShowingError = true
            errorMessage = error.localizedDescription
        }
    }
}

struct MessageView: View {
    let message: Message
    @StateObject private var chatService = ChatService.shared
    @State private var isPlayingVoice = false
    
    var body: some View {
        HStack {
            if message.isUser {
                Spacer()
            }
            
            VStack(alignment: message.isUser ? .trailing : .leading) {
                switch message.type {
                case .text:
                    Text(message.content)
                        .padding()
                        .background(message.isUser ? Color.blue : Color.gray.opacity(0.2))
                        .foregroundColor(message.isUser ? .white : .primary)
                        .cornerRadius(16)
                
                case .image:
                    if let imageUrl = message.imageUrl {
                        AsyncImage(url: URL(string: imageUrl)) { phase in
                            switch phase {
                            case .empty:
                                ProgressView()
                            case .success(let image):
                                image
                                    .resizable()
                                    .scaledToFit()
                                    .frame(maxWidth: 200)
                                    .cornerRadius(16)
                            case .failure:
                                Image(systemName: "photo")
                                    .foregroundColor(.gray)
                            @unknown default:
                                EmptyView()
                            }
                        }
                    }
                
                case .voice:
                    if let voiceUrl = message.voiceUrl {
                        Button(action: {
                            Task {
                                await playVoice(voiceUrl)
                            }
                        }) {
                            HStack {
                                Image(systemName: isPlayingVoice ? "stop.circle.fill" : "play.circle.fill")
                                Text(message.content)
                            }
                            .padding()
                            .background(message.isUser ? Color.blue : Color.gray.opacity(0.2))
                            .foregroundColor(message.isUser ? .white : .primary)
                            .cornerRadius(16)
                        }
                    }
                }
            }
            
            if !message.isUser {
                Spacer()
            }
        }
    }
    
    private func playVoice(_ url: String) async {
        do {
            isPlayingVoice = true
            try await chatService.playVoiceMessage(url: url)
            isPlayingVoice = false
        } catch {
            isPlayingVoice = false
            print("播放语音失败: \(error)")
        }
    }
}

#Preview {
    NavigationView {
        ChatView()
    }
} 