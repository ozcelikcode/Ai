package database

import (
	"blog/internal/models"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"golang.org/x/crypto/bcrypt"
)

var DB *gorm.DB

func Connect() error {
	var err error
	DB, err = gorm.Open(sqlite.Open("blog.db"), &gorm.Config{})
	if err != nil {
		return err
	}

	err = DB.AutoMigrate(&models.User{}, &models.Post{})
	if err != nil {
		return err
	}

	return createDefaultAdmin()
}

func createDefaultAdmin() error {
	var count int64
	DB.Model(&models.User{}).Where("is_admin = ?", true).Count(&count)
	
	if count == 0 {
		hashedPassword, err := bcrypt.GenerateFromPassword([]byte("12345678"), bcrypt.DefaultCost)
		if err != nil {
			return err
		}

		admin := models.User{
			Username: "admin",
			Password: string(hashedPassword),
			IsAdmin:  true,
		}

		return DB.Create(&admin).Error
	}

	return nil
}