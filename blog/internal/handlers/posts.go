package handlers

import (
	"blog/internal/database"
	"blog/internal/models"
	"net/http"
	"strings"
	"time"
	"github.com/gin-gonic/gin"
)

type PostRequest struct {
	Title     string `json:"title" binding:"required"`
	Content   string `json:"content" binding:"required"`
	Excerpt   string `json:"excerpt"`
	Published bool   `json:"published"`
}

func GetPosts(c *gin.Context) {
	var posts []models.Post
	query := database.DB.Preload("Author").Order("created_at DESC")
	
	if c.Query("published") == "true" {
		query = query.Where("published = ?", true)
	}

	if err := query.Find(&posts).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch posts"})
		return
	}

	c.JSON(http.StatusOK, posts)
}

func GetPost(c *gin.Context) {
	id := c.Param("id")
	var post models.Post
	
	if err := database.DB.Preload("Author").First(&post, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Post not found"})
		return
	}

	c.JSON(http.StatusOK, post)
}

func GetPostBySlug(c *gin.Context) {
	slug := c.Param("slug")
	var post models.Post
	
	query := database.DB.Preload("Author").Where("slug = ?", slug)
	if !isAdmin(c) {
		query = query.Where("published = ?", true)
	}
	
	if err := query.First(&post).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Post not found"})
		return
	}

	c.JSON(http.StatusOK, post)
}

func CreatePost(c *gin.Context) {
	var req PostRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	userID, _ := c.Get("userID")
	
	post := models.Post{
		Title:     req.Title,
		Slug:      generateSlug(req.Title),
		Content:   req.Content,
		Excerpt:   req.Excerpt,
		AuthorID:  userID.(uint),
		Published: req.Published,
	}

	if req.Published {
		now := time.Now()
		post.PublishedAt = &now
	}

	if err := database.DB.Create(&post).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create post"})
		return
	}

	database.DB.Preload("Author").First(&post, post.ID)
	c.JSON(http.StatusCreated, post)
}

func UpdatePost(c *gin.Context) {
	id := c.Param("id")
	var post models.Post
	
	if err := database.DB.First(&post, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Post not found"})
		return
	}

	var req PostRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	wasPublished := post.Published
	post.Title = req.Title
	post.Slug = generateSlug(req.Title)
	post.Content = req.Content
	post.Excerpt = req.Excerpt
	post.Published = req.Published

	if !wasPublished && req.Published {
		now := time.Now()
		post.PublishedAt = &now
	}

	if err := database.DB.Save(&post).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update post"})
		return
	}

	database.DB.Preload("Author").First(&post, post.ID)
	c.JSON(http.StatusOK, post)
}

func DeletePost(c *gin.Context) {
	id := c.Param("id")
	var post models.Post
	
	if err := database.DB.First(&post, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Post not found"})
		return
	}

	if err := database.DB.Delete(&post).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete post"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Post deleted successfully"})
}

func generateSlug(title string) string {
	slug := strings.ToLower(title)
	slug = strings.ReplaceAll(slug, " ", "-")
	slug = strings.ReplaceAll(slug, "ı", "i")
	slug = strings.ReplaceAll(slug, "ş", "s")
	slug = strings.ReplaceAll(slug, "ğ", "g")
	slug = strings.ReplaceAll(slug, "ü", "u")
	slug = strings.ReplaceAll(slug, "ö", "o")
	slug = strings.ReplaceAll(slug, "ç", "c")
	return slug
}

func isAdmin(c *gin.Context) bool {
	isAdmin, exists := c.Get("isAdmin")
	return exists && isAdmin.(bool)
}