// 🐍 Combined_Outreach_All — Using Python ETL Output
// Simplified M code that reads from centralized Python ETL CSV output
// Maintains exact same column structure for Power BI compatibility
let
    // === 1. Dynamic File Path Discovery ===
    // Look for the most recent Python ETL output file
    OutputFolder = "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\Community_Engagement\output\",
    
    // Try to find the most recent community_engagement_data_*.csv file
    // Pattern: community_engagement_data_YYYYMMDD_HHMMSS.csv
    PythonETLFile = try 
        let
            // Get all CSV files in the output directory
            Source = Folder.Files(OutputFolder),
            FilteredFiles = Table.SelectRows(Source, each Text.StartsWith([Name], "community_engagement_data_") and Text.EndsWith([Name], ".csv")),
            SortedFiles = Table.Sort(FilteredFiles, {{"Date modified", Order.Descending}}),
            LatestFile = if Table.RowCount(SortedFiles) > 0 
                        then OutputFolder & SortedFiles{0}[Name]
                        else error "No Python ETL output files found"
        in
            LatestFile
    otherwise
        // Fallback to a specific filename pattern if dynamic discovery fails
        OutputFolder & "community_engagement_combined_" & Date.ToText(DateTime.Date(DateTime.LocalNow()), "yyyy-MM-dd") & ".csv",

    // === 2. Read Python ETL CSV Output ===
    CSVSource = Csv.Document(File.Contents(PythonETLFile), [Delimiter=",", Columns=null, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    HeadersPromoted = Table.PromoteHeaders(CSVSource, [PromoteAllScalars=true]),
    
    // === 3. Data Type Transformations ===
    // Handle datetime strings from Python ETL (format: "YYYY-MM-DD HH:MM:SS")
    DateParsed = Table.TransformColumns(HeadersPromoted, {
        {"date", each 
            if _ = null or _ = "" 
            then null 
            else try DateTime.Date(DateTime.FromText(_)) otherwise Date.FromText(Text.Start(_, 10)), 
        type date}
    }),
    
    // Handle time columns safely (may be in various formats from Python)
    TimeParsed = Table.TransformColumns(DateParsed, {
        {"start_time", each try Time.FromText(_) otherwise null, type time},
        {"end_time", each try Time.FromText(_) otherwise null, type time}
    }),
    
    TypedData = Table.TransformColumnTypes(TimeParsed, {
        {"event_name", type text},
        {"location", type text},
        {"duration_hours", type number},
        {"attendee_count", Int64.Type},
        {"office", type text},
        {"division", type text}
    }),
    
    // Handle any duration_hours conversion issues (Python ETL may have NaNs)
    SafeDuration = Table.TransformColumns(TypedData, {
        {"duration_hours", each 
            if _ = null or _ = "" or Text.From(_) = "nan" 
            then 0.5 
            else try Number.From(_) otherwise 0.5, type number}
    }),
    
    // Handle any attendee_count conversion issues  
    SafeAttendees = Table.TransformColumns(SafeDuration, {
        {"attendee_count", each try Number.From(_) otherwise 1, Int64.Type}
    }),
    
    // === 4. Column Selection and Renaming ===
    // Select only the columns needed for Power BI
    SelectedColumns = Table.SelectColumns(SafeAttendees, {
        "date",
        "duration_hours", 
        "event_name",
        "location",
        "attendee_count",
        "office"
    }),
    
    // Rename columns to match exact Power BI expectations
    RenamedColumns = Table.RenameColumns(SelectedColumns, {
        {"date", "Date"},
        {"duration_hours", "Event Duration (Hours)"},
        {"event_name", "Event Name"}, 
        {"location", "Location of Event"},
        {"attendee_count", "Number of Police Department Attendees"},
        {"office", "Office"}
    }),
    
    // === 5. Data Quality and Filtering ===
    // Remove rows with null dates (same as original M code)
    FilteredData = Table.SelectRows(RenamedColumns, each [Date] <> null),
    
    // Ensure Event Duration is reasonable (0.1 to 24 hours)
    ValidatedDuration = Table.TransformColumns(FilteredData, {
        {"Event Duration (Hours)", each 
            if _ = null or _ <= 0 then 0.5
            else if _ > 24 then 8.0  
            else Number.Round(_, 2), 
        type number}
    }),
    
    // Ensure attendee count is at least 1 if null/zero
    ValidatedAttendees = Table.TransformColumns(ValidatedDuration, {
        {"Number of Police Department Attendees", each 
            if _ = null or _ <= 0 then 1 else _, 
        Int64.Type}
    }),
    
    // === 6. Final Sort and Output ===
    // Sort by date ascending (same as original M code)
    FinalData = if Table.RowCount(ValidatedAttendees) > 0 
                then Table.Sort(ValidatedAttendees, {{"Date", Order.Ascending}}) 
                else ValidatedAttendees

in
    FinalData