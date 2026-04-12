package examplefunc

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type Stats struct {
	Language string
	Files    int
	Lines    int
}

var extMap = map[string]string{
	".go":   "Go",
	".md":   "Markdown",
	".yaml": "YAML",
	".yml":  "YAML",
	".json": "JSON",
	".py":   "Python",
	".rs":   "Rust",
	".js":   "JavaScript",
	".ts":   "TypeScript",
}

func Run(path string, excludes []string) ([]Stats, error) {
	counts := make(map[string]*Stats)

	err := filepath.Walk(path, func(p string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.IsDir() {
			for _, ex := range excludes {
				if info.Name() == ex {
					return filepath.SkipDir
				}
			}
			return nil
		}

		ext := filepath.Ext(p)
		lang, ok := extMap[ext]
		if !ok {
			return nil
		}

		data, err := os.ReadFile(p)
		if err != nil {
			return nil
		}
		lines := len(strings.Split(string(data), "\n"))

		if counts[lang] == nil {
			counts[lang] = &Stats{Language: lang}
		}
		counts[lang].Files++
		counts[lang].Lines += lines

		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("walk path: %w", err)
	}

	result := make([]Stats, 0, len(counts))
	for _, s := range counts {
		result = append(result, *s)
	}
	return result, nil
}
