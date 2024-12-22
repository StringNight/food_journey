import LocalAuthentication
import Foundation

enum BiometricType {
    case none
    case touchID
    case faceID
    
    var description: String {
        switch self {
        case .none:
            return "不支持"
        case .touchID:
            return "Touch ID"
        case .faceID:
            return "Face ID"
        }
    }
}

enum BiometricError: LocalizedError {
    case notAvailable
    case notEnrolled
    case canceled
    case failed
    
    var errorDescription: String? {
        switch self {
        case .notAvailable:
            return "设备不支持生物认证"
        case .notEnrolled:
            return "未设置生物认证"
        case .canceled:
            return "用户取消认证"
        case .failed:
            return "认证失败"
        }
    }
}

@MainActor
class BiometricAuthUtil {
    static let shared = BiometricAuthUtil()
    private let context = LAContext()
    
    private init() {}
    
    var biometricType: BiometricType {
        var error: NSError?
        
        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            return .none
        }
        
        switch context.biometryType {
        case .touchID:
            return .touchID
        case .faceID:
            return .faceID
        default:
            return .none
        }
    }
    
    func authenticate() async throws {
        var error: NSError?
        
        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            if let error = error as? LAError {
                switch error.code {
                case .biometryNotAvailable:
                    throw BiometricError.notAvailable
                case .biometryNotEnrolled:
                    throw BiometricError.notEnrolled
                default:
                    throw BiometricError.failed
                }
            }
            throw BiometricError.failed
        }
        
        let reason = "使用\(biometricType.description)快速登录"
        
        do {
            try await context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: reason)
        } catch let error as LAError {
            switch error.code {
            case .userCancel:
                throw BiometricError.canceled
            case .biometryNotAvailable:
                throw BiometricError.notAvailable
            case .biometryNotEnrolled:
                throw BiometricError.notEnrolled
            default:
                throw BiometricError.failed
            }
        }
    }
} 