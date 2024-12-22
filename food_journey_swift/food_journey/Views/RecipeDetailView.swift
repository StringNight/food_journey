import SwiftUI

struct RecipeDetailView: View {
    let recipe: Recipe
    @StateObject private var recipeService = RecipeService.shared
    @State private var showingRatingSheet = false
    @State private var rating: Int = 0
    @State private var comment: String = ""
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var isFavorite: Bool = false
    
    private let imageHeight: CGFloat = 300
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // 食谱图片
                if let imageUrl = recipe.imageUrl,
                   let url = URL(string: imageUrl) {
                    AsyncImage(url: url) { image in
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                            .frame(height: imageHeight)
                            .clipped()
                    } placeholder: {
                        Rectangle()
                            .fill(Color.gray.opacity(0.2))
                            .frame(height: imageHeight)
                            .overlay {
                                Image(systemName: "photo")
                                    .foregroundColor(.gray)
                            }
                    }
                }
                
                VStack(alignment: .leading, spacing: 12) {
                    // 标题和收藏按钮
                    HStack {
                        Text(recipe.title)
                            .font(.title)
                            .fontWeight(.bold)
                        
                        Spacer()
                        
                        Button(action: toggleFavorite) {
                            Image(systemName: isFavorite ? "heart.fill" : "heart")
                                .foregroundColor(isFavorite ? .red : .gray)
                                .font(.title2)
                        }
                    }
                    
                    // 基本信息
                    HStack(spacing: 16) {
                        if let cookingTime = recipe.cookingTime {
                            InfoItem(icon: "clock", text: "\(cookingTime)分钟")
                        }
                        if let difficulty = recipe.difficulty {
                            InfoItem(icon: "chart.bar", text: difficulty)
                        }
                        InfoItem(icon: "flame", text: "\(Int(recipe.nutrition.calories))卡路里")
                    }
                    
                    // 标签
                    if let tags = recipe.tags {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack {
                                ForEach(tags, id: \.self) { tag in
                                    Text(tag)
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 6)
                                        .background(Color.blue.opacity(0.1))
                                        .foregroundColor(.blue)
                                        .cornerRadius(16)
                                }
                            }
                        }
                    }
                    
                    Divider()
                    
                    // 食材
                    VStack(alignment: .leading, spacing: 8) {
                        Text("食材")
                            .font(.title2)
                            .fontWeight(.bold)
                        
                        ForEach(recipe.ingredients, id: \.name) { ingredient in
                            HStack {
                                Text("•")
                                Text(ingredient.name)
                                Spacer()
                                Text("\(ingredient.amount)\(ingredient.unit ?? "")")
                                    .foregroundColor(.gray)
                            }
                        }
                    }
                    
                    Divider()
                    
                    // 步骤
                    VStack(alignment: .leading, spacing: 12) {
                        Text("步骤")
                            .font(.title2)
                            .fontWeight(.bold)
                        
                        ForEach(recipe.steps, id: \.stepNumber) { step in
                            VStack(alignment: .leading, spacing: 8) {
                                HStack(alignment: .top) {
                                    Text("\(step.stepNumber).")
                                        .font(.headline)
                                        .foregroundColor(.blue)
                                    Text(step.description)
                                }
                                
                                if let tips = step.tips {
                                    Text("提示：\(tips)")
                                        .font(.caption)
                                        .foregroundColor(.gray)
                                }
                                
                                if let imageUrl = step.image,
                                   let url = URL(string: imageUrl) {
                                    AsyncImage(url: url) { image in
                                        image
                                            .resizable()
                                            .aspectRatio(contentMode: .fit)
                                            .cornerRadius(8)
                                    } placeholder: {
                                        Rectangle()
                                            .fill(Color.gray.opacity(0.2))
                                            .aspectRatio(16/9, contentMode: .fit)
                                            .overlay {
                                                Image(systemName: "photo")
                                                    .foregroundColor(.gray)
                                            }
                                    }
                                }
                            }
                        }
                    }
                    
                    Divider()
                    
                    // 营养信息
                    VStack(alignment: .leading, spacing: 8) {
                        Text("营养信息")
                            .font(.title2)
                            .fontWeight(.bold)
                        
                        Group {
                            NutritionRow(label: "热量", value: "\(Int(recipe.nutrition.calories))卡路里")
                            NutritionRow(label: "蛋白质", value: "\(recipe.nutrition.protein)克")
                            NutritionRow(label: "碳水化合物", value: "\(recipe.nutrition.carbs)克")
                            NutritionRow(label: "脂肪", value: "\(recipe.nutrition.fat)克")
                            if let fiber = recipe.nutrition.fiber {
                                NutritionRow(label: "膳食纤维", value: "\(fiber)克")
                            }
                        }
                        
                        if let vitamins = recipe.nutrition.vitamins {
                            ForEach(Array(vitamins.sorted(by: { $0.key < $1.key })), id: \.key) { key, value in
                                NutritionRow(label: key, value: "\(value)克")
                            }
                        }
                    }
                }
                .padding()
            }
        }
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button(action: { showingRatingSheet = true }) {
                    Image(systemName: "star")
                }
            }
        }
        .sheet(isPresented: $showingRatingSheet) {
            RatingView(rating: $rating, comment: $comment, onSubmit: {
                Task {
                    await submitRating()
                }
            })
        }
        .alert("错误", isPresented: $showError) {
            Button("确定", role: .cancel) {}
        } message: {
            Text(errorMessage)
        }
        .task {
            isFavorite = recipeService.favoriteRecipes.contains { $0.id == recipe.id }
        }
    }
    
    private func toggleFavorite() {
        Task {
            do {
                if isFavorite {
                    try await recipeService.removeFromFavorites(recipeId: recipe.id)
                } else {
                    try await recipeService.addToFavorites(recipeId: recipe.id)
                }
                isFavorite.toggle()
            } catch {
                showError = true
                errorMessage = error.localizedDescription
            }
        }
    }
    
    private func submitRating() async {
        do {
            try await recipeService.rateRecipe(recipeId: recipe.id, rating: rating, comment: comment.isEmpty ? nil : comment)
            showingRatingSheet = false
            rating = 0
            comment = ""
        } catch {
            showError = true
            errorMessage = error.localizedDescription
        }
    }
}

struct InfoItem: View {
    let icon: String
    let text: String
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(.blue)
            Text(text)
                .foregroundColor(.gray)
        }
    }
}

struct NutritionRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text(label)
            Spacer()
            Text(value)
                .foregroundColor(.gray)
        }
    }
}

struct RatingView: View {
    @Environment(\.dismiss) private var dismiss
    @Binding var rating: Int
    @Binding var comment: String
    let onSubmit: () -> Void
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("评分")) {
                    HStack {
                        ForEach(1...5, id: \.self) { number in
                            Image(systemName: number <= rating ? "star.fill" : "star")
                                .foregroundColor(.yellow)
                                .onTapGesture {
                                    rating = number
                                }
                        }
                    }
                }
                
                Section(header: Text("评论")) {
                    TextEditor(text: $comment)
                        .frame(height: 100)
                }
            }
            .navigationTitle("评价食谱")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("取消") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("提交") {
                        onSubmit()
                    }
                    .disabled(rating == 0)
                }
            }
        }
    }
} 