import Foundation
import UIKit
import AVFoundation

@MainActor
class ChatService: ObservableObject {
    static let shared = ChatService()
    private let networkService = NetworkService.shared
    
    @Published var messages: [Message] = []
    @Published var isRecording = false
    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?
    
    private init() {}
    
    // 发送文本消息
    func sendTextMessage(_ text: String) async throws -> Message {
        let request = FoodJourneyModels.ChatTextRequest(message: text)
        let response: FoodJourneyModels.MessageResponse = try await networkService.request(
            endpoint: "/chat/text",
            method: "POST",
            body: try JSONEncoder().encode(request),
            requiresAuth: true
        )
        
        let userMessage = Message(
            id: UUID().uuidString,
            type: .text,
            content: text,
            timestamp: Date(),
            isUser: true
        )
        
        let botMessage = Message(
            id: UUID().uuidString,
            type: .text,
            content: response.message,
            timestamp: Date(),
            isUser: false,
            imageUrl: response.image_url,
            voiceUrl: response.voice_url
        )
        
        messages.append(contentsOf: [userMessage, botMessage])
        return botMessage
    }
    
    // 发送图片消息
    func sendImageMessage(_ image: UIImage) async throws -> Message {
        let imageUrl = try await networkService.uploadImage(image, endpoint: "/chat/image")
        let request = FoodJourneyModels.ChatImageRequest(image_url: imageUrl)
        
        let response: FoodJourneyModels.MessageResponse = try await networkService.request(
            endpoint: "/chat/image/analyze",
            method: "POST",
            body: try JSONEncoder().encode(request),
            requiresAuth: true
        )
        
        let userMessage = Message(
            id: UUID().uuidString,
            type: .image,
            content: "",
            timestamp: Date(),
            isUser: true,
            imageUrl: imageUrl
        )
        
        let botMessage = Message(
            id: UUID().uuidString,
            type: .text,
            content: response.message,
            timestamp: Date(),
            isUser: false,
            imageUrl: response.image_url,
            voiceUrl: response.voice_url
        )
        
        messages.append(contentsOf: [userMessage, botMessage])
        return botMessage
    }
    
    // 开始录音
    func startRecording() throws {
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playAndRecord, mode: .default)
        try audioSession.setActive(true)
        
        let documentPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let audioFilename = documentPath.appendingPathComponent("\(UUID().uuidString).m4a")
        
        let settings = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 12000,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]
        
        audioRecorder = try AVAudioRecorder(url: audioFilename, settings: settings)
        audioRecorder?.record()
        isRecording = true
    }
    
    // 停止录音并发送
    func stopRecordingAndSend() async throws -> Message? {
        guard let recorder = audioRecorder else { return nil }
        
        recorder.stop()
        isRecording = false
        
        let audioUrl = recorder.url
        let audioData = try Data(contentsOf: audioUrl)
        
        // 上传音频文件
        let uploadResponse = try await networkService.uploadAudio(
            audioData,
            filename: audioUrl.lastPathComponent,
            endpoint: "/chat/voice"
        )
        
        // 发送语音识别请求
        let request = FoodJourneyModels.ChatVoiceRequest(voice_url: uploadResponse.url)
        let response: FoodJourneyModels.MessageResponse = try await networkService.request(
            endpoint: "/chat/voice/transcribe",
            method: "POST",
            body: try JSONEncoder().encode(request),
            requiresAuth: true
        )
        
        let userMessage = Message(
            id: UUID().uuidString,
            type: .voice,
            content: response.message,
            timestamp: Date(),
            isUser: true,
            voiceUrl: uploadResponse.url
        )
        
        let botMessage = Message(
            id: UUID().uuidString,
            type: .text,
            content: response.message,
            timestamp: Date(),
            isUser: false,
            imageUrl: response.image_url,
            voiceUrl: response.voice_url
        )
        
        messages.append(contentsOf: [userMessage, botMessage])
        return botMessage
    }
    
    // 播放语音消息
    func playVoiceMessage(url: String) async throws {
        guard let url = URL(string: url) else { return }
        
        let (data, _) = try await URLSession.shared.data(from: url)
        audioPlayer = try AVAudioPlayer(data: data)
        audioPlayer?.play()
    }
    
    // 取消录音
    func cancelRecording() {
        audioRecorder?.stop()
        audioRecorder?.deleteRecording()
        isRecording = false
    }
    
    // 清空消息历史
    func clearMessages() {
        messages.removeAll()
    }
} 
