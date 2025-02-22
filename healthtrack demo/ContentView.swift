import SwiftUI

/*
 后端接口说明：
 URL: https://api.mybackend.com/profile
 请求方式: GET
 返回数据示例:
 {
   "name": "Tianxin",
   "goalProgress": 0.8,
   "shortTermGoal": "增加5kg肌肉",
   "longTermGoal": "体脂降至15%"
 }
*/

// 用户资料数据模型
struct UserProfile: Codable {
    let name: String            // 用户名
    let goalProgress: Double    // 目标完成进度（0-1）
    let shortTermGoal: String   // 短期目标
    let longTermGoal: String    // 长期目标
}

// 视图模型，负责与后端交互获取用户资料
class ProfileViewModel: ObservableObject {
    @Published var profile: UserProfile?
    
    // 调用后端接口获取用户资料
    func fetchUserProfile() {
        guard let url = URL(string: "https://api.mybackend.com/profile") else {
            print("错误：URL格式不正确")
            return
        }
        let task = URLSession.shared.dataTask(with: url) { data, response, error in
            if let error = error {
                print("网络请求错误: \(error.localizedDescription)")
                return
            }
            guard let data = data else {
                print("错误：未返回数据")
                return
            }
            do {
                let decoder = JSONDecoder()
                let profile = try decoder.decode(UserProfile.self, from: data)
                DispatchQueue.main.async {
                    self.profile = profile
                }
            } catch {
                print("数据解析错误: \(error.localizedDescription)")
            }
        }
        task.resume()
    }
}

struct ContentView: View {
    // 使用视图模型管理用户资料
    @StateObject private var viewModel = ProfileViewModel()
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading) {
                    
                    // 顶部区域：用户头像、昵称及目标进度
                    HStack(alignment: .center) {
                        NavigationLink(destination: ProfileView()) {
                            Image(systemName: "person.crop.circle")
                                .resizable()
                                .frame(width: 60, height: 60)
                                .padding()
                        }
                        VStack(alignment: .leading, spacing: 8) {
                            // 动态显示用户名称，若数据未加载则显示"加载中..."
                            Text(viewModel.profile?.name ?? "加载中...")
                                .font(.title2)
                                .bold()
                            // 根据后端返回的进度数据显示目标进度
                            if let progress = viewModel.profile?.goalProgress {
                                ProgressView("目标进度: \(Int(progress*100))%", value: progress, total: 1.0)
                                    .progressViewStyle(LinearProgressViewStyle(tint: .blue))
                            } else {
                                ProgressView("加载中", value: 0, total: 1.0)
                                    .progressViewStyle(LinearProgressViewStyle(tint: .blue))
                            }
                        }
                        Spacer()
                    }
                    .padding(.horizontal)
                    
                    // 目标描述，使用后端返回的目标数据
                    VStack(alignment: .leading, spacing: 4) {
                        Text("短期目标: \(viewModel.profile?.shortTermGoal ?? "加载中...")")
                        Text("长期目标: \(viewModel.profile?.longTermGoal ?? "加载中...")")
                    }
                    .padding(.horizontal)
                    .padding(.bottom, 20)
                    
                    // 卡片区域
                    VStack(spacing: 20) {
                        NavigationLink(destination: BodyDataDetailView()) {
                            CardView(title: "身体数据",
                                     subtitle: "体重: 72kg, 体脂率: 20%",
                                     icon: "heart.fill")
                        }
                        NavigationLink(destination: TrainingProgressDetailView()) {
                            CardView(title: "训练进度",
                                     subtitle: "今日: 腿部训练，完成3/5组深蹲",
                                     icon: "figure.walk")
                        }
                        NavigationLink(destination: DietDetailView()) {
                            CardView(title: "饮食情况",
                                     subtitle: "摄入: 1500 kcal, 蛋白质: 100g",
                                     icon: "leaf.fill")
                        }
                        NavigationLink(destination: RecoveryDetailView()) {
                            CardView(title: "恢复状态",
                                     subtitle: "睡眠: 7小时, 疲劳感: 4/5",
                                     icon: "bed.double.fill")
                        }
                    }
                    .padding(.horizontal)
                    
                    Spacer()
                }
                // 当视图加载时调用后端接口获取用户资料
                .onAppear {
                    viewModel.fetchUserProfile()
                }
                .navigationTitle("健身追踪器")
            }
        }
    }
}

struct CardView: View {
    var title: String
    var subtitle: String
    var icon: String
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .font(.system(size: 40))
                .foregroundColor(.white)
                .padding()
                .background(Color.blue)
                .cornerRadius(10)
            VStack(alignment: .leading) {
                Text(title)
                    .font(.headline)
                Text(subtitle)
                    .font(.subheadline)
                    .foregroundColor(.gray)
            }
            Spacer()
            Image(systemName: "chevron.right")
                .foregroundColor(.gray)
        }
        .padding()
        .background(Color(UIColor.secondarySystemBackground))
        .cornerRadius(10)
        .shadow(color: Color.black.opacity(0.1), radius: 5, x: 0, y: 2)
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
