import Foundation

public enum FoodJourneyModels {
    // MARK: - 响应模型
    public struct EmptyResponse: Codable {}

//    public struct ErrorResponse: Codable {
//        public let detail: String
//    }

    public struct FileUploadResponse: Codable {
        public let url: String
    }

    public struct ChatResponse: Codable {
        public let response: String
        public let success: Bool
    }

    public struct AudioUploadResponse: Codable {
        public let url: String
    }

    public struct MessageResponse: Codable {
        public let message: String
        public let suggestions: [String]?
        public let image_url: String?
        public let voice_url: String?
    }

    public struct RecipeSearchResponse: Codable {
        public let recipes: [Recipe]
        public let total: Int
        public let page: Int
        public let total_pages: Int
        
        enum CodingKeys: String, CodingKey {
            case recipes
            case total
            case page
            case total_pages = "total_pages"
        }
    }

    // MARK: - 请求模型
    public struct ChatTextRequest: Codable {
        public let message: String
        
        public init(message: String) {
            self.message = message
        }
    }

    public struct ChatImageRequest: Codable {
        public let image_url: String
        
        public init(image_url: String) {
            self.image_url = image_url
        }
    }

    public struct ChatVoiceRequest: Codable {
        public let voice_url: String
        
        public init(voice_url: String) {
            self.voice_url = voice_url
        }
    }

    public struct RecipeRatingRequest: Codable {
        public let rating: Int
        public let comment: String?
        
        public init(rating: Int, comment: String?) {
            self.rating = rating
            self.comment = comment
        }
    }

    public struct PasswordResetRequest: Codable {
        public let email: String
        
        public init(email: String) {
            self.email = email
        }
    }

    public struct ChangePasswordRequest: Codable {
        public let current_password: String
        public let new_password: String
        
        public init(current_password: String, new_password: String) {
            self.current_password = current_password
            self.new_password = new_password
        }
    }
} 
