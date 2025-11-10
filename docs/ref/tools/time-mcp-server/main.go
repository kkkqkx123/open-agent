package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

// TimeResult represents time information in a specific timezone
type TimeResult struct {
	Timezone string `json:"timezone"`
	Datetime string `json:"datetime"`
	IsDST    bool   `json:"is_dst"`
}

// TimeConversionResult represents the result of a time conversion between two timezones
type TimeConversionResult struct {
	Source         TimeResult `json:"source"`
	Target         TimeResult `json:"target"`
	TimeDifference string     `json:"time_difference"`
}

// TimeServer contains all operations for handling time functionality
type TimeServer struct {
	localTimezone string
}

// NewTimeServer creates a new TimeServer instance
func NewTimeServer(localTimezone string) *TimeServer {
	// If local timezone is not provided, try to determine it
	if localTimezone == "" {
		localTimezone = getLocalTimezone()
	}

	return &TimeServer{
		localTimezone: localTimezone,
	}
}

// getLocalTimezone tries to determine the local timezone
func getLocalTimezone() string {
	// Get local timezone from the system
	tz, offset := time.Now().Zone()

	// If we got a non-empty zone name, return it
	if tz != "" && tz != "Local" {
		return tz
	}

	// Otherwise, construct a timezone string from the offset
	hours := offset / 3600
	mins := (offset % 3600) / 60

	if mins == 0 {
		return fmt.Sprintf("UTC%+d", hours)
	}
	return fmt.Sprintf("UTC%+d:%02d", hours, mins)
}

// GetCurrentTime returns the current time in the specified timezone
func (s *TimeServer) GetCurrentTime(timezone string) (TimeResult, error) {
	// If timezone is not provided, use local timezone
	if timezone == "" {
		timezone = s.localTimezone
	}

	// Load timezone location
	loc, err := time.LoadLocation(timezone)
	if err != nil {
		return TimeResult{}, fmt.Errorf("invalid timezone: %v", err)
	}

	// Get current time in the specified timezone
	currentTime := time.Now().In(loc)

	// Determine if DST is in effect
	_, offset := currentTime.Zone()
	_, stdOffset := time.Date(currentTime.Year(), 1, 1, 0, 0, 0, 0, loc).Zone()
	isDST := offset != stdOffset

	return TimeResult{
		Timezone: timezone,
		Datetime: currentTime.Format(time.RFC3339),
		IsDST:    isDST,
	}, nil
}

// ConvertTime converts a time from one timezone to another
func (s *TimeServer) ConvertTime(sourceTimezone, timeStr, targetTimezone string) (TimeConversionResult, error) {
	// If timezones are not provided, use local timezone
	if sourceTimezone == "" {
		sourceTimezone = s.localTimezone
	}
	if targetTimezone == "" {
		targetTimezone = s.localTimezone
	}

	// Load source timezone location
	sourceLoc, err := time.LoadLocation(sourceTimezone)
	if err != nil {
		return TimeConversionResult{}, fmt.Errorf("invalid source timezone: %v", err)
	}

	// Load target timezone location
	targetLoc, err := time.LoadLocation(targetTimezone)
	if err != nil {
		return TimeConversionResult{}, fmt.Errorf("invalid target timezone: %v", err)
	}

	// Parse the time string (HH:MM format)
	timeParts := strings.Split(timeStr, ":")
	if len(timeParts) != 2 {
		return TimeConversionResult{}, fmt.Errorf("invalid time format: expected HH:MM [24-hour format]")
	}

	hour, err := stringToInt(timeParts[0])
	if err != nil || hour < 0 || hour > 23 {
		return TimeConversionResult{}, fmt.Errorf("invalid hour: expected 0-23")
	}

	minute, err := stringToInt(timeParts[1])
	if err != nil || minute < 0 || minute > 59 {
		return TimeConversionResult{}, fmt.Errorf("invalid minute: expected 0-59")
	}

	// Create time in source timezone
	now := time.Now()
	sourceTime := time.Date(now.Year(), now.Month(), now.Day(), hour, minute, 0, 0, sourceLoc)

	// Convert to target timezone
	targetTime := sourceTime.In(targetLoc)

	// Calculate time difference
	_, sourceOffset := sourceTime.Zone()
	_, targetOffset := targetTime.Zone()

	hoursDifference := float64(targetOffset-sourceOffset) / 3600.0

	// Format time difference string
	timeDiffStr := ""
	if hoursDifference == float64(int(hoursDifference)) {
		// Whole hours
		timeDiffStr = fmt.Sprintf("%+.1fh", hoursDifference)
	} else {
		// Fractional hours (like UTC+5:45)
		timeDiffStr = fmt.Sprintf("%+.2fh", hoursDifference)
		// Remove trailing zeros
		timeDiffStr = strings.TrimRight(timeDiffStr, "0")
		timeDiffStr = strings.TrimRight(timeDiffStr, ".")
	}

	// Determine if DST is in effect for source timezone
	_, stdSourceOffset := time.Date(sourceTime.Year(), 1, 1, 0, 0, 0, 0, sourceLoc).Zone()
	sourceIsDST := sourceOffset != stdSourceOffset

	// Determine if DST is in effect for target timezone
	_, stdTargetOffset := time.Date(targetTime.Year(), 1, 1, 0, 0, 0, 0, targetLoc).Zone()
	targetIsDST := targetOffset != stdTargetOffset

	return TimeConversionResult{
		Source: TimeResult{
			Timezone: sourceTimezone,
			Datetime: sourceTime.Format(time.RFC3339),
			IsDST:    sourceIsDST,
		},
		Target: TimeResult{
			Timezone: targetTimezone,
			Datetime: targetTime.Format(time.RFC3339),
			IsDST:    targetIsDST,
		},
		TimeDifference: timeDiffStr,
	}, nil
}

// Helper function to convert string to int
func stringToInt(s string) (int, error) {
	var result int
	_, err := fmt.Sscanf(s, "%d", &result)
	return result, err
}

// Version information
const (
	version = "0.2.0"
	appName = "Time MCP Server"
)

// printVersion prints version information
func printVersion() {
	fmt.Printf("%s version %s\n", appName, version)
}

// printUsage prints a custom usage message
func printUsage() {
	fmt.Fprintf(os.Stderr, "Usage: %s [options]\n\n", os.Args[0])
	fmt.Fprintf(os.Stderr, "%s is a Model Context Protocol server that provides time and timezone conversion functionality.\n\n", appName)
	fmt.Fprintf(os.Stderr, "Options:\n")
	flag.PrintDefaults()
}

func main() {
	var transport string
	var localTimezone string
	var port int = 8080
	var showVersion bool
	var showHelp bool

	// Override the default usage message
	flag.Usage = printUsage

	// Define command-line flags
	flag.StringVar(&transport, "transport", "stdio", "Transport type (stdio or sse)")
	flag.StringVar(&transport, "t", "stdio", "Transport type (stdio or sse)")
	flag.StringVar(&localTimezone, "local-timezone", "", "Override local timezone")
	flag.StringVar(&localTimezone, "l", "", "Override local timezone")
	flag.IntVar(&port, "port", 8080, "Port for SSE transport")
	flag.IntVar(&port, "p", 8080, "Port for SSE transport")
	flag.BoolVar(&showVersion, "version", false, "Show version information and exit")
	flag.BoolVar(&showVersion, "v", false, "Show version information and exit")
	flag.BoolVar(&showHelp, "help", false, "Show this help message and exit")
	flag.BoolVar(&showHelp, "h", false, "Show this help message and exit")

	flag.Parse()

	// Handle version flag
	if showVersion {
		printVersion()
		os.Exit(0)
	}

	// Handle help flag
	if showHelp {
		printUsage()
		os.Exit(0)
	}

	// Create time server
	timeServer := NewTimeServer(localTimezone)

	// Create a new MCP server
	s := server.NewMCPServer(
		appName,
		version,
		server.WithResourceCapabilities(true, true),
		server.WithLogging(),
	)

	// Add get_current_time tool
	getCurrentTimeTool := mcp.NewTool("get_current_time",
		mcp.WithDescription("Get current time in a specific timezones"),
		mcp.WithString("timezone",
			mcp.Required(),
			mcp.Description(fmt.Sprintf("IANA timezone name (e.g., 'America/New_York', 'Europe/London'). Use '%s' as local timezone if no timezone provided by the user.", timeServer.localTimezone)),
		),
	)

	// Add convert_time tool
	convertTimeTool := mcp.NewTool("convert_time",
		mcp.WithDescription("Convert time between timezones"),
		mcp.WithString("source_timezone",
			mcp.Required(),
			mcp.Description(fmt.Sprintf("Source IANA timezone name (e.g., 'America/New_York', 'Europe/London'). Use '%s' as local timezone if no source timezone provided by the user.", timeServer.localTimezone)),
		),
		mcp.WithString("time",
			mcp.Required(),
			mcp.Description("Time to convert in 24-hour format (HH:MM)"),
		),
		mcp.WithString("target_timezone",
			mcp.Required(),
			mcp.Description(fmt.Sprintf("Target IANA timezone name (e.g., 'Asia/Tokyo', 'America/San_Francisco'). Use '%s' as local timezone if no target timezone provided by the user.", timeServer.localTimezone)),
		),
	)

	// Add handlers for get_current_time tool
	s.AddTool(getCurrentTimeTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		timezone, ok := request.Params.Arguments["timezone"].(string)
		if !ok {
			return nil, errors.New("missing required parameter: timezone")
		}

		// Get current time
		result, err := timeServer.GetCurrentTime(timezone)
		if err != nil {
			return nil, err
		}

		// Convert result to JSON
		resultJSON, err := json.MarshalIndent(result, "", "  ")
		if err != nil {
			return nil, err
		}

		return mcp.NewToolResultText(string(resultJSON)), nil
	})

	// Add handlers for convert_time tool
	s.AddTool(convertTimeTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		sourceTimezone, ok := request.Params.Arguments["source_timezone"].(string)
		if !ok {
			return nil, errors.New("missing required parameter: source_timezone")
		}

		timeStr, ok := request.Params.Arguments["time"].(string)
		if !ok {
			return nil, errors.New("missing required parameter: time")
		}

		targetTimezone, ok := request.Params.Arguments["target_timezone"].(string)
		if !ok {
			return nil, errors.New("missing required parameter: target_timezone")
		}

		// Convert time
		result, err := timeServer.ConvertTime(sourceTimezone, timeStr, targetTimezone)
		if err != nil {
			return nil, err
		}

		// Convert result to JSON
		resultJSON, err := json.MarshalIndent(result, "", "  ")
		if err != nil {
			return nil, err
		}

		return mcp.NewToolResultText(string(resultJSON)), nil
	})

	if transport == "stdio" {
		fmt.Fprintln(os.Stderr, "Time MCP Server running on stdio")
		if err := server.ServeStdio(s); err != nil {
			fmt.Fprintf(os.Stderr, "Server error: %v\n", err)
		}
	} else if transport == "sse" {
		fmt.Fprintln(os.Stderr, "Time MCP Server running on SSE")
		sseServer := server.NewSSEServer(s, server.WithBaseURL(fmt.Sprintf("http://localhost:%d", port)))
		log.Printf("Server started listening on :%d\n", port)
		if err := sseServer.Start(fmt.Sprintf(":%d", port)); err != nil {
			log.Fatalf("Failed to start server: %v", err)
		}
	}
}