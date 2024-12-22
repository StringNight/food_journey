import Foundation

extension FoodJourneyModels {
    struct LoginRequest: Codable {
        let username: String
        let password: String
    }

    struct RegisterRequest: Codable {
        let username: String
        let password: String
        let confirm_password: String
        let email: String
    }

    struct AuthResponse: Codable {
        let access_token: String
        let token_type: String
        let user: UserProfile
        
        enum CodingKeys: String, CodingKey {
            case access_token = "access_token"
            case token_type = "token_type"
            case user = "user"
        }
    }

    struct UserProfile: Codable {
        let id: Int
        let username: String
        let email: String
        let created_at: Date
        let avatar_url: String?
        
        enum CodingKeys: String, CodingKey {
            case id = "id"
            case username = "username"
            case email = "email"
            case created_at = "created_at"
            case avatar_url = "avatar_url"
        }
    }

    struct ErrorResponse: Codable {
        let detail: String
    }
} 
