import SwiftUI

struct ProfileView: View {
    var body: some View {
        Text("个人档案页面")
            .font(.title)
            .navigationTitle("个人档案")
    }
}

struct ProfileView_Previews: PreviewProvider {
    static var previews: some View {
        ProfileView()
    }
}
