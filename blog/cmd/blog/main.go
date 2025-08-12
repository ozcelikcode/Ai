package main

import (
	"blog/internal/database"
	"blog/internal/handlers"
	"blog/internal/middleware"
	"log"
	"net/http"
	"github.com/gin-gonic/gin"
)

func main() {
	if err := database.Connect(); err != nil {
		log.Fatal("Failed to connect to database:", err)
	}

	r := gin.Default()
	
	r.LoadHTMLGlob("web/templates/*")
	r.Static("/static", "./web/static")

	// Web routes
	r.GET("/", func(c *gin.Context) {
		c.HTML(http.StatusOK, "index.html", gin.H{
			"Title": "Ana Sayfa",
		})
	})
	
	r.GET("/post/:slug", func(c *gin.Context) {
		c.HTML(http.StatusOK, "post.html", gin.H{
			"Title": "Yazı",
		})
	})
	
	r.GET("/admin", func(c *gin.Context) {
		c.HTML(http.StatusOK, "admin.html", gin.H{
			"Title": "Admin Panel",
		})
	})

	// API routes
	api := r.Group("/api")
	{
		// Auth routes
		api.POST("/auth/login", handlers.Login)
		
		// Public post routes
		api.GET("/posts", handlers.GetPosts)
		api.GET("/posts/:id", handlers.GetPost)
		api.GET("/posts/slug/:slug", handlers.GetPostBySlug)
		
		// Protected routes
		protected := api.Group("")
		protected.Use(middleware.AuthRequired())
		{
			// Admin routes
			admin := protected.Group("")
			admin.Use(middleware.AdminRequired())
			{
				admin.POST("/posts", handlers.CreatePost)
				admin.PUT("/posts/:id", handlers.UpdatePost)
				admin.DELETE("/posts/:id", handlers.DeletePost)
			}
		}
	}

	log.Println("Server starting on :8081")
	log.Fatal(r.Run(":8081"))
}