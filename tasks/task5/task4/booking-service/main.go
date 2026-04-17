package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
)

func main() {
	enableFeatureX := os.Getenv("ENABLE_FEATURE_X") == "true"
	checkHeader := os.Getenv("ENABLE_HEADER_FEATURE") == "true"

	http.HandleFunc("/ping", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "pong")
	})

	http.HandleFunc("/feature", func(w http.ResponseWriter, r *http.Request) {
		enabled := enableFeatureX
		if checkHeader {
			enabled = enabled || (r.Header.Get("X-Feature-Enabled") == "true")
		}
		if enabled {
			fmt.Fprintf(w, "Feature X is enabled!\n")
		} else {
			w.WriteHeader(http.StatusNotFound)
			fmt.Fprintf(w, "Feature X disabled\n")
		}
	})

	log.Println("Server running on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}