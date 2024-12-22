import SwiftUI

struct RecipeListView: View {
    @StateObject private var recipeService = RecipeService.shared
    @State private var searchText = ""
    @State private var showingError = false
    @State private var errorMessage = ""
    @State private var isLoading = false
    
    private let columns = [
        GridItem(.flexible()),
        GridItem(.flexible())
    ]
    
    var body: some View {
        NavigationView {
            ScrollView {
                if isLoading {
                    ProgressView()
                        .padding()
                } else {
                    LazyVGrid(columns: columns, spacing: 16) {
                        ForEach(recipeService.recipes) { recipe in
                            NavigationLink(destination: RecipeDetailView(recipe: recipe)) {
                                RecipeCard(recipe: recipe)
                            }
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("美食食谱")
            .searchable(text: $searchText, prompt: "搜索食谱")
            .onChange(of: searchText) { newValue in
                Task {
                    await searchRecipes(query: newValue)
                }
            }
            .refreshable {
                await loadRecipes()
            }
            .alert("错误", isPresented: $showingError) {
                Button("确定", role: .cancel) {}
            } message: {
                Text(errorMessage)
            }
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        // TODO: 添加新食谱
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
        }
        .task {
            await loadRecipes()
        }
    }
    
    private func loadRecipes() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            _ = try await recipeService.fetchRecipes()
        } catch {
            showingError = true
            errorMessage = error.localizedDescription
        }
    }
    
    private func searchRecipes(query: String) async {
        guard !query.isEmpty else {
            await loadRecipes()
            return
        }
        
        isLoading = true
        defer { isLoading = false }
        
        do {
            _ = try await recipeService.searchRecipes(query: query)
        } catch {
            showingError = true
            errorMessage = error.localizedDescription
        }
    }
}

struct RecipeCard: View {
    let recipe: Recipe
    
    var body: some View {
        VStack(alignment: .leading) {
            if let imageUrl = recipe.imageUrl, let url = URL(string: imageUrl) {
                AsyncImage(url: url) { image in
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                } placeholder: {
                    Rectangle()
                        .fill(Color.gray.opacity(0.2))
                }
                .frame(height: 150)
                .clipped()
            } else {
                Rectangle()
                    .fill(Color.gray.opacity(0.2))
                    .frame(height: 150)
                    .overlay {
                        Image(systemName: "photo")
                            .foregroundColor(.gray)
                    }
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(recipe.title)
                    .font(.headline)
                    .lineLimit(2)
                
                if let difficulty = recipe.difficulty {
                    Label(difficulty, systemImage: "star.fill")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                if let cookingTime = recipe.cookingTime {
                    Label("\(cookingTime) 分钟", systemImage: "clock.fill")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
        }
        .background(Color.white)
        .cornerRadius(10)
        .shadow(radius: 2)
    }
}

#Preview {
    RecipeListView()
} 
