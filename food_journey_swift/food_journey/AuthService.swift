import Foundation
import UIKit
import SwiftUI

@MainActor
class AuthService: ObservableObject {
    static let shared = AuthService()
    private let networkService = NetworkService.shared
    
    @Published var isAuthenticated = false
    @Published var currentUser: FoodJourneyModels.UserProfile?
    @AppStorage("auth_token") private var authToken: String = ""
    @AppStorage("remember_username") private var rememberedUsername: String = ""
    @AppStorage("use_biometric") private var useBiometric: Bool = false
    
    private init() {
        isAuthenticated = !authToken.isEmpty
        if isAuthenticated {
            Task {
                await fetchUserProfile()
            }
        }
    }
    
    func login(username: String, password: String, rememberMe: Bool) async throws {
        let loginRequest = FoodJourneyModels.LoginRequest(username: username, password: password)
        let response: FoodJourneyModels.AuthResponse = try await networkService.request(
            endpoint: "/auth/login/json",
            method: "POST",
            body: try JSONEncoder().encode(loginRequest)
        )
        
        authToken = response.access_token
        currentUser = response.user
        isAuthenticated = true
        
        if rememberMe {
            rememberedUsername = username
            try await storeCredentials(username: username, password: password)
        }
    }
    
    func loginWithBiometric() async throws {
        guard !rememberedUsername.isEmpty else {
            throw AuthError.noBiometricCredentials
        }
        
        // 验证生物识别
        try await BiometricAuthUtil.shared.authenticate()
        
        // 获取保存的密码
        guard let password = try? KeychainManager.shared.get(for: rememberedUsername) else {
            throw AuthError.noBiometricCredentials
        }
        
        // 使用保存的凭证登录
        try await login(username: rememberedUsername, password: password, rememberMe: true)
    }
    
    func register(username: String, password: String, email: String) async throws {
        let registerRequest = FoodJourneyModels.RegisterRequest(
            username: username,
            password: password,
            confirm_password: password,
            email: email
        )
        
        let response: FoodJourneyModels.AuthResponse = try await networkService.request(
            endpoint: "/auth/register",
            method: "POST",
            body: try JSONEncoder().encode(registerRequest)
        )
        print(response)
        
        authToken = response.access_token
        print(authToken)
        currentUser = response.user
        isAuthenticated = true
    }
    
    func resetPassword(email: String) async throws {
        let request = FoodJourneyModels.PasswordResetRequest(email: email)
        let _: FoodJourneyModels.EmptyResponse = try await networkService.request(
            endpoint: "/auth/reset-password",
            method: "POST",
            body: try JSONEncoder().encode(request)
        )
    }
    
    func changePassword(currentPassword: String, newPassword: String) async throws {
        let request = FoodJourneyModels.ChangePasswordRequest(
            current_password: currentPassword,
            new_password: newPassword
        )
        let _: FoodJourneyModels.EmptyResponse = try await networkService.request(
            endpoint: "/auth/change-password",
            method: "POST",
            body: try JSONEncoder().encode(request),
            requiresAuth: true
        )
    }
    
    func uploadAvatar(image: UIImage) async throws {
        let url = try await networkService.uploadImage(image, endpoint: "/auth/avatar")
        // 更新用户信息
        await fetchUserProfile()
    }
    
    func logout() {
        authToken = ""
        currentUser = nil
        isAuthenticated = false
        
        if !rememberedUsername.isEmpty {
            try? KeychainManager.shared.delete(for: rememberedUsername)
            rememberedUsername = ""
        }
    }
    
    private func fetchUserProfile() async {
        do {
            let profile: FoodJourneyModels.UserProfile = try await networkService.request(
                endpoint: "/auth/profile",
                method: "GET",
                requiresAuth: true
            )
            currentUser = profile
        } catch {
            logout()
        }
    }
    
    private func storeCredentials(username: String, password: String) async throws {
        try KeychainManager.shared.save(password, for: username)
    }
}

enum AuthError: LocalizedError {
    case noBiometricCredentials
    case biometricAuthFailed
    case invalidCredentials
    case networkError
    
    var errorDescription: String? {
        switch self {
        case .noBiometricCredentials:
            return "没有找到生物识别凭证"
        case .biometricAuthFailed:
            return "生物识别认证失败"
        case .invalidCredentials:
            return "用户名或密码错误"
        case .networkError:
            return "网络连接失败"
        }
    }
}
