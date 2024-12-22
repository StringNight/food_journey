import SwiftUI

struct LoginView: View {
    @StateObject private var authService = AuthService.shared
    @State private var username = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var email = ""
    @State private var isRegistering = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var rememberMe = false
    @State private var showResetPassword = false
    @State private var resetEmail = ""
    @State private var showBiometricButton = false
    @State private var isLoading = false
    
    var body: some View {
        NavigationView {
            ZStack {
                ScrollView {
                    VStack(spacing: 20) {
                        Image(systemName: "person.circle.fill")
                            .resizable()
                            .frame(width: 100, height: 100)
                            .foregroundColor(.blue)
                            .padding(.bottom, 20)
                        
                        if !isRegistering && !showResetPassword {
                            if showBiometricButton {
                                Button(action: biometricLogin) {
                                    Label(
                                        BiometricAuthUtil.shared.biometricType == .faceID ? "Face ID 登录" : "Touch ID 登录",
                                        systemImage: BiometricAuthUtil.shared.biometricType == .faceID ? "faceid" : "touchid"
                                    )
                                    .frame(maxWidth: .infinity)
                                    .padding()
                                    .background(Color.green)
                                    .foregroundColor(.white)
                                    .cornerRadius(10)
                                }
                                .disabled(isLoading)
                            }
                        }
                        
                        if showResetPassword {
                            resetPasswordView
                        } else {
                            loginRegisterView
                        }
                    }
                    .padding()
                }
                .scrollDismissesKeyboard(.immediately)
                
                if isLoading {
                    ProgressView()
                        .scaleEffect(1.5)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(Color.black.opacity(0.2))
                }
            }
            .alert("错误", isPresented: $showError) {
                Button("确定", role: .cancel) {}
            } message: {
                Text(errorMessage)
            }
            .navigationTitle(isRegistering ? "注册" : (showResetPassword ? "重置密码" : "登录"))
            .onAppear {
                checkBiometricAvailability()
            }
        }
    }
    
    private var loginRegisterView: some View {
        VStack {
            TextField("用户名", text: $username)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .autocapitalization(.none)
                .textContentType(.username)
            
            if isRegistering {
                TextField("邮箱", text: $email)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .autocapitalization(.none)
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
            }
            
            SecureField("密码", text: $password)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .textContentType(isRegistering ? .newPassword : .password)
            
            if isRegistering {
                SecureField("确认密码", text: $confirmPassword)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .textContentType(.newPassword)
            }
            
            if !isRegistering {
                Toggle("记住我", isOn: $rememberMe)
                    .padding(.vertical, 5)
            }
            
            Button(action: {
                Task {
                    await handleLoginRegister()
                }
            }) {
                Text(isRegistering ? "注册" : "登录")
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
            .disabled(isLoading || username.isEmpty || password.isEmpty || 
                     (isRegistering && (email.isEmpty || confirmPassword.isEmpty)))
            
            if !isRegistering {
                Button("忘记密码？") {
                    showResetPassword = true
                }
                .foregroundColor(.blue)
                .padding(.top, 10)
            }
            
            Button(action: {
                isRegistering.toggle()
                clearFields()
            }) {
                Text(isRegistering ? "已有账号？登录" : "没有账号？注册")
                    .foregroundColor(.blue)
            }
            .padding(.top, 10)
        }
    }
    
    private var resetPasswordView: some View {
        VStack {
            TextField("邮箱", text: $resetEmail)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .autocapitalization(.none)
                .textContentType(.emailAddress)
                .keyboardType(.emailAddress)
            
            Button(action: {
                Task {
                    await resetPassword()
                }
            }) {
                Text("发送重置链接")
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
            .disabled(isLoading || resetEmail.isEmpty)
            
            Button("返回登录") {
                showResetPassword = false
                resetEmail = ""
            }
            .foregroundColor(.blue)
            .padding(.top, 10)
        }
    }
    
    private func checkBiometricAvailability() {
        showBiometricButton = BiometricAuthUtil.shared.biometricType != .none
    }
    
    private func biometricLogin() {
        Task {
            await handleBiometricLogin()
        }
    }
    
    private func handleBiometricLogin() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            try await authService.loginWithBiometric()
        } catch {
            showError = true
            errorMessage = error.localizedDescription
        }
    }
    
    private func handleLoginRegister() async {
        if isRegistering {
            // 验证邮箱格式
            let emailRegex = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}"
            let emailPredicate = NSPredicate(format:"SELF MATCHES %@", emailRegex)
            guard emailPredicate.evaluate(with: email) else {
                showError = true
                errorMessage = "邮箱格式不正确"
                return
            }
            
            // 验证密码匹配
            guard password == confirmPassword else {
                showError = true
                errorMessage = "两次输入的密码不匹配"
                return
            }
        }
        
        isLoading = true
        defer { isLoading = false }
        
        do {
            if isRegistering {
                try await authService.register(username: username, password: password, email: email)
            } else {
                try await authService.login(username: username, password: password, rememberMe: rememberMe)
            }
            clearFields()
        } catch {
            showError = true
            errorMessage = error.localizedDescription
        }
    }
    
    private func resetPassword() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            try await authService.resetPassword(email: resetEmail)
            showResetPassword = false
            resetEmail = ""
        } catch {
            showError = true
            errorMessage = error.localizedDescription
        }
    }
    
    private func clearFields() {
        username = ""
        password = ""
        confirmPassword = ""
        email = ""
    }
}

#Preview {
    LoginView()
} 
