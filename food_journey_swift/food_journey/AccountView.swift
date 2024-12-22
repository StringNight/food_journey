import SwiftUI

struct AccountView: View {
    @StateObject private var authService = AuthService.shared
    @State private var showImagePicker = false
    @State private var selectedImage: UIImage?
    @State private var isUploading = false
    @State private var showError = false
    @State private var errorMessage = ""
    @AppStorage("use_biometric") private var useBiometric = false
    @State private var showChangePassword = false
    
    var body: some View {
        NavigationView {
            Form {
                UserProfileSection(
                    authService: authService,
                    showImagePicker: $showImagePicker,
                    isUploading: $isUploading,
                    selectedImage: $selectedImage
                )

                Section(header: Text("安全设置")) {
                    if BiometricAuthUtil.shared.biometricType != .none {
                        Toggle(isOn: $useBiometric) {
                            Label(
                                BiometricAuthUtil.shared.biometricType == .faceID ? "使用 Face ID" : "使用 Touch ID",
                                systemImage: BiometricAuthUtil.shared.biometricType == .faceID ? "faceid" : "touchid"
                            )
                        }
                    }

                    NavigationLink(destination: ChangePasswordView()) {
                        Label("修改密码", systemImage: "lock")
                    }
                }

                Section {
                    Button(action: logout) {
                        HStack {
                            Spacer()
                            Text("退出登录")
                                .foregroundColor(.red)
                            Spacer()
                        }
                    }
                }
            }
            .navigationTitle("账户")
            .sheet(isPresented: $showImagePicker) {
                ImagePicker(image: $selectedImage)
            }
            .onChange(of: selectedImage) { newImage in
                if let image = newImage {
                    Task {
                        await uploadAvatar(image)
                    }
                }
            }
            .alert(isPresented: $showError) {
                Alert(
                    title: Text("错误"),
                    message: Text(errorMessage),
                    dismissButton: .default(Text("确定"))
                )
            }
        }
    }
    
    private func uploadAvatar(_ image: UIImage) async {
        isUploading = true
        defer { isUploading = false }
        
        do {
            try await authService.uploadAvatar(image: image)
            selectedImage = nil
        } catch {
            showError = true
            errorMessage = error.localizedDescription
        }
    }
    
    private func logout() {
        authService.logout()
    }
}


struct UserProfileSection: View {
    @ObservedObject var authService: AuthService
    @Binding var showImagePicker: Bool
    @Binding var isUploading: Bool
    @Binding var selectedImage: UIImage?

    var body: some View {
//        Section(header: Text("个人信息")) {
            HStack {
                Spacer()
                VStack {
                    if let user = authService.currentUser {
                        AsyncImage(url: URL(string: user.avatar_url ?? "")) { phase in
                            switch phase {
                            case .empty:
                                ProgressView()
                            case .success(let image):
                                image
                                    .resizable()
                                    .scaledToFill()
                            case .failure:
                                Image(systemName: "person.circle.fill")
                                    .resizable()
                                    .foregroundColor(.gray)
                            @unknown default:
                                EmptyView()
                            }
                        }
                        .frame(width: 100, height: 100)
                        .clipShape(Circle())
                        .overlay(Circle().stroke(Color.gray, lineWidth: 2))

                        Button(action: {
                            showImagePicker = true
                        }) {
                            Text(isUploading ? "上传中..." : "更换头像")
                        }
                        .disabled(isUploading)
                    }
                }
                Spacer()
            }
            .padding(.vertical)

            if let user = authService.currentUser {
                HStack {
                    Text("用户名")
                    Spacer()
                    Text(user.username)
                        .foregroundColor(.gray)
                }

                HStack {
                    Text("邮箱")
                    Spacer()
                    Text(user.email)
                        .foregroundColor(.gray)
                }

                HStack {
                    Text("注册时间")
                    Spacer()
                    Text(formatDate(user.created_at))
                        .foregroundColor(.gray)
                }
            }
        }
//    }
}

public func formatDate(_ date: Date) -> String {
    let formatter = DateFormatter()
    formatter.dateFormat = "yyyy-MM-dd HH:mm"
    return formatter.string(from: date)
}

#Preview {
    AccountView()
}
