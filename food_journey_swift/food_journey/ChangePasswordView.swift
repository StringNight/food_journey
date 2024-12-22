import SwiftUI

struct ChangePasswordView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var authService = AuthService.shared
    @State private var currentPassword = ""
    @State private var newPassword = ""
    @State private var confirmPassword = ""
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var isLoading = false
    
    var body: some View {
        Form {
            Section(header: Text("修改密码")) {
                SecureField("当前密码", text: $currentPassword)
                    .textContentType(.password)
                SecureField("新密码", text: $newPassword)
                    .textContentType(.newPassword)
                SecureField("确认新密码", text: $confirmPassword)
                    .textContentType(.newPassword)
            }
            
            Section {
                Button(action: {
                    Task {
                        await changePassword()
                    }
                }) {
                    if isLoading {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle())
                    } else {
                        Text("确认修改")
                    }
                }
                .frame(maxWidth: .infinity)
                .disabled(isLoading || currentPassword.isEmpty || newPassword.isEmpty || confirmPassword.isEmpty)
            }
        }
        .navigationTitle("修改密码")
        .alert("错误", isPresented: $showError) {
            Button("确定", role: .cancel) {}
        } message: {
            Text(errorMessage)
        }
    }
    
    private func changePassword() async {
        guard newPassword == confirmPassword else {
            showError = true
            errorMessage = "两次输入的新密码不一致"
            return
        }
        
        isLoading = true
        defer { isLoading = false }
        
        do {
            try await authService.changePassword(currentPassword: currentPassword, newPassword: newPassword)
            dismiss()
        } catch {
            showError = true
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    NavigationView {
        ChangePasswordView()
    }
} 
