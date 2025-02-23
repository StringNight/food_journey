import SwiftUI

struct DietDetailView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("饮食详情")
                    .font(.title)
                    .bold()
                
                // 今日饮食记录
                VStack(alignment: .leading, spacing: 8) {
                    Text("今日饮食记录")
                        .font(.headline)
                    Text("早餐: 鸡蛋、全麦面包、牛奶")
                    Text("午餐: 鸡肉沙拉、米饭")
                    Text("晚餐: 鱼类、蔬菜")
                }
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                // 营养分析与建议
                VStack(alignment: .leading, spacing: 8) {
                    Text("营养分析")
                        .font(.headline)
                    Text("热量: 1500 kcal (目标: 2000 kcal)")
                    Text("蛋白质: 100g")
                    Text("脂肪: 50g")
                    Text("碳水化合物: 150g")
                    Text("建议: 增加蛋白质摄入，可以加餐鸡胸肉或蛋白粉。")
                }
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                // 历史趋势（图表占位符）
                Text("饮食趋势（过去7天）")
                    .font(.headline)
                Rectangle()
                    .fill(Color.gray.opacity(0.3))
                    .frame(height: 200)
                    .overlay(Text("图表占位符"))
                    .cornerRadius(10)
                
                // 食物替代建议
                VStack(alignment: .leading, spacing: 8) {
                    Text("食物替代建议")
                        .font(.headline)
                    Text("可以用豆腐替代鸡胸肉。")
                }
                .padding()
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(10)
                
                Spacer()
            }
            .padding()
        }
        .navigationTitle("饮食详情")
    }
}

struct DietDetailView_Previews: PreviewProvider {
    static var previews: some View {
        DietDetailView()
    }
}
