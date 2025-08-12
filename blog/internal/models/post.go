package models

import (
	"time"
	"gorm.io/gorm"
)

type Post struct {
	ID          uint           `gorm:"primarykey" json:"id"`
	Title       string         `gorm:"not null" json:"title"`
	Slug        string         `gorm:"uniqueIndex;not null" json:"slug"`
	Content     string         `gorm:"type:text;not null" json:"content"`
	Excerpt     string         `gorm:"type:text" json:"excerpt"`
	AuthorID    uint           `gorm:"not null" json:"author_id"`
	Author      User           `gorm:"foreignKey:AuthorID" json:"author"`
	Published   bool           `gorm:"default:false" json:"published"`
	PublishedAt *time.Time     `json:"published_at"`
	CreatedAt   time.Time      `json:"created_at"`
	UpdatedAt   time.Time      `json:"updated_at"`
	DeletedAt   gorm.DeletedAt `gorm:"index" json:"-"`
}