import SwiftUI

struct ChatList: View {
    var body: some View {
        NavigationSplitView {
            List() {
                NavigationLink {
                    ContentView()
                }
                label: {
                    ChatRow()
                }
            }.navigationTitle("Chat")
        }detail: {
            Text("Select a Landmark")
        }
    }
}


#Preview {
    ChatList()
}
