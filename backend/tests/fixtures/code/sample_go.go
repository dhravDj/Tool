package main

import (
	"fmt"
	"net/http"
	"github.com/gin-gonic/gin"
)

type ServerConfig struct {
	Port int
	Host string
}

func (s *ServerConfig) GetAddress() string {
	return fmt.Sprintf("%s:%d", s.Host, s.Port)
}

func StartServer(cfg ServerConfig) {
	r := gin.Default()
	r.GET("/ping", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "pong"})
	})
	r.Run(cfg.GetAddress())
}
