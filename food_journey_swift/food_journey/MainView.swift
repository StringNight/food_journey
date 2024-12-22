import SwiftUI

struct MainView: View {
    @StateObject private var authService = AuthService.shared
    
    var body: some View {
        Group {
            if authService.isAuthenticated {
                TabView {
                    NavigationView {
                        ChatView()
                    }
                    .tabItem {
                        Label("聊天", systemImage: "message.fill")
                    }
                    
                    NavigationView {
                        RecipeListView()
                    }
                    .tabItem {
                        Label("食谱", systemImage: "book.fill")
                    }
                    
                    NavigationView {
                        AccountView()
                    }
                    .tabItem {
                        Label("账户", systemImage: "person.crop.circle.fill")
                    }
                }
            } else {
                LoginView()
            }
        }
    }
}

#Preview {
    MainView()
}
