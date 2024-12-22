import Foundation
import UIKit

class NetworkService {
    static let shared = NetworkService()
    private let baseURL = "http://127.0.0.1:8000/api"
    
    private init() {
        dateFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        dateFormatter.locale = Locale(identifier: "en_US_POSIX")
        dateFormatter.timeZone = TimeZone(secondsFromGMT: 0)
    }
    
    private let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        return formatter
    }()
    
    func request<T: Codable>(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil,
        requiresAuth: Bool = false
    ) async throws -> T {
        guard let url = URL(string: baseURL + endpoint) else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if requiresAuth {
            if let token = UserDefaults.standard.string(forKey: "auth_token") {
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            }
        }
        
        if let body = body {
            request.httpBody = body
            if let jsonString = String(data: body, encoding: .utf8) {
                print("Request Body: \(jsonString)")
            }
        }
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        if let jsonString = String(data: data, encoding: .utf8) {
            print("Response Data: \(jsonString)")
        }
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        
        if !(200...299).contains(httpResponse.statusCode) {
            if let errorResponse = try? JSONDecoder().decode(FoodJourneyModels.ErrorResponse.self, from: data) {
                print("Error Response: \(errorResponse.detail)")
                throw NetworkError.serverError(errorResponse.detail)
            }
            throw NetworkError.serverError("请求失败: \(httpResponse.statusCode)")
        }
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)
            
            if let date = self.dateFormatter.date(from: dateString) {
                return date
            }
            
            let fallbackFormatter = DateFormatter()
            fallbackFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSZ"
            fallbackFormatter.locale = Locale(identifier: "en_US_POSIX")
            
            if let date = fallbackFormatter.date(from: dateString) {
                return date
            }
            
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date string \(dateString)")
        }
        
        do {
            let decodedResponse = try decoder.decode(T.self, from: data)
            return decodedResponse
        } catch {
            print("解码错误: \(error)")
            if let jsonString = String(data: data, encoding: .utf8) {
                print("原始JSON数据: \(jsonString)")
            }
            throw error
        }
    }
    
    private func decodeAuthResponse(data: Data) throws -> FoodJourneyModels.AuthResponse {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        do {
            let response = try decoder.decode(FoodJourneyModels.AuthResponse.self, from: data)
            print("成功解码 AuthResponse:")
            print("- access_token: \(response.access_token)")
            print("- token_type: \(response.token_type)")
            print("- user.id: \(response.user.id)")
            print("- user.username: \(response.user.username)")
            print("- user.email: \(response.user.email)")
            print("- user.created_at: \(response.user.created_at)")
            if let avatarUrl = response.user.avatar_url {
                print("- user.avatar_url: \(avatarUrl)")
            }
            return response
        } catch let DecodingError.dataCorrupted(context) {
            print("数据损坏: \(context)")
            throw NetworkError.decodingError("数据损坏: \(context)")
        } catch let DecodingError.keyNotFound(key, context) {
            print("未找到键 \(key): \(context)")
            throw NetworkError.decodingError("未找到键 \(key)")
        } catch let DecodingError.valueNotFound(value, context) {
            print("未找到值 \(value): \(context)")
            throw NetworkError.decodingError("未找到值 \(value)")
        } catch let DecodingError.typeMismatch(type, context) {
            print("类型不匹配 \(type): \(context)")
            throw NetworkError.decodingError("类型不匹配 \(type)")
        } catch {
            print("其他解码错误: \(error)")
            throw NetworkError.decodingError("解码失败: \(error.localizedDescription)")
        }
    }
    
    func sendChatMessage(_ message: String) async throws -> FoodJourneyModels.MessageResponse {
        let request = FoodJourneyModels.ChatTextRequest(message: message)
        return try await self.request(
            endpoint: "/chat/text",
            method: "POST",
            body: try JSONEncoder().encode(request),
            requiresAuth: true
        )
    }
    
    func sendChatImage(_ imageUrl: String) async throws -> FoodJourneyModels.MessageResponse {
        let request = FoodJourneyModels.ChatImageRequest(image_url: imageUrl)
        return try await self.request(
            endpoint: "/chat/image",
            method: "POST",
            body: try JSONEncoder().encode(request),
            requiresAuth: true
        )
    }
    
    func sendChatVoice(_ voiceUrl: String) async throws -> FoodJourneyModels.MessageResponse {
        let request = FoodJourneyModels.ChatVoiceRequest(voice_url: voiceUrl)
        return try await self.request(
            endpoint: "/chat/voice",
            method: "POST",
            body: try JSONEncoder().encode(request),
            requiresAuth: true
        )
    }
    
    private func uploadFile(_ fileData: Data, filename: String, mimeType: String, endpoint: String) async throws -> String {
        guard let url = URL(string: baseURL + endpoint) else {
            throw NetworkError.invalidURL
        }
        
        let boundary = UUID().uuidString
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        if let token = UserDefaults.standard.string(forKey: "auth_token") {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        var body = Data()
        
        // 添加文件数据
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n".data(using: .utf8)!)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = body
        
        let (responseData, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.serverError("上传失败")
        }
        
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let result = try decoder.decode(FoodJourneyModels.FileUploadResponse.self, from: responseData)
        return result.url
    }
    
    func uploadImage(_ image: UIImage, endpoint: String) async throws -> String {
        guard let imageData = image.jpegData(compressionQuality: 0.8) else {
            throw NetworkError.serverError("图片处理失败")
        }
        return try await uploadFile(imageData, filename: "image.jpg", mimeType: "image/jpeg", endpoint: endpoint)
    }
    
    func uploadAudio(_ audioData: Data, filename: String, endpoint: String) async throws -> FoodJourneyModels.AudioUploadResponse {
        let url = try await uploadFile(audioData, filename: filename, mimeType: "audio/m4a", endpoint: endpoint)
        return FoodJourneyModels.AudioUploadResponse(url: url)
    }
}

enum NetworkError: Error {
    case invalidURL
    case invalidResponse
    case noData
    case serverError(String)
    case decodingError(String)
}

//extension FoodJourneyModels {
//    struct ChatRequest: Codable {
//        let message: String
//    }
//} 
