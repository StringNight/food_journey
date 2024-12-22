import Foundation

enum MessageType: String, Codable {
    case text
    case image
    case voice
}

struct Message: Identifiable, Codable {
    let id: String
    let type: MessageType
    let content: String
    let timestamp: Date
    let isUser: Bool
    var imageUrl: String?
    var voiceUrl: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case type
        case content
        case timestamp
        case isUser = "is_user"
        case imageUrl = "image_url"
        case voiceUrl = "voice_url"
    }
} 