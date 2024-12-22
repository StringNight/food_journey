import Foundation

@MainActor
class RecipeService: ObservableObject {
    static let shared = RecipeService()
    private let networkService = NetworkService.shared
    
    @Published var recipes: [Recipe] = []
    @Published var favoriteRecipes: [Recipe] = []
    @Published var searchResults: [Recipe] = []
    @Published var isSearching = false
    
    private init() {}
    
    func fetchRecipes() async throws {
        let response: [Recipe] = try await networkService.request(
            endpoint: "/recipes",
            requiresAuth: true
        )
        recipes = response
    }
    
    func fetchFavoriteRecipes() async throws {
        let response: [Recipe] = try await networkService.request(
            endpoint: "/recipes/favorites",
            requiresAuth: true
        )
        favoriteRecipes = response
    }
    
    func searchRecipes(query: String, page: Int = 1, limit: Int = 20) async throws {
        guard !query.isEmpty else {
            searchResults = []
            return
        }
        
        isSearching = true
        defer { isSearching = false }
        
        let encodedQuery = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        let response: FoodJourneyModels.RecipeSearchResponse = try await networkService.request(
            endpoint: "/recipes/search?query=\(encodedQuery)&page=\(page)&limit=\(limit)",
            requiresAuth: true
        )
        
        if page == 1 {
            searchResults = response.recipes
        } else {
            searchResults.append(contentsOf: response.recipes)
        }
    }
    
    func addToFavorites(recipeId: String) async throws {
        let _: FoodJourneyModels.EmptyResponse = try await networkService.request(
            endpoint: "/recipes/\(recipeId)/favorite",
            method: "POST",
            requiresAuth: true
        )
        // 更新本地收藏列表
        if let recipe = recipes.first(where: { recipe in recipe.id == recipeId }) {
            favoriteRecipes.append(recipe)
        }
    }
    
    func removeFromFavorites(recipeId: String) async throws {
        let _: FoodJourneyModels.EmptyResponse = try await networkService.request(
            endpoint: "/recipes/\(recipeId)/favorite",
            method: "DELETE",
            requiresAuth: true
        )
        // 从本地收藏列表中移除
        favoriteRecipes.removeAll { $0.id == recipeId }
    }
    
    func rateRecipe(recipeId: String, rating: Int, comment: String?) async throws {
        let ratingData = FoodJourneyModels.RecipeRatingRequest(rating: rating, comment: comment)
        let _: FoodJourneyModels.EmptyResponse = try await networkService.request(
            endpoint: "/recipes/\(recipeId)/rate",
            method: "POST",
            body: try JSONEncoder().encode(ratingData),
            requiresAuth: true
        )
    }
} 