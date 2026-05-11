param (
        [Parameter(Mandatory=$true)][string]$server,
        [Parameter(Mandatory=$true)][string]$api_key
        )

Function ignore_cert_error {if (-not("dummy" -as [type]))
    {add-type -TypeDefinition @"
    using System;
    using System.Net;
    using System.Net.Security;
    using System.Security.Cryptography.X509Certificates;

    public static class Dummy {
        public static bool ReturnTrue(object sender,
            X509Certificate certificate,
            X509Chain chain,
            SslPolicyErrors sslPolicyErrors) { return true; }

        public static RemoteCertificateValidationCallback GetDelegate() {
            return new RemoteCertificateValidationCallback(Dummy.ReturnTrue);
        }
    }
"@
    }
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = [dummy]::GetDelegate()
    }


Function web_request($resource) {
	$Retries = 3
	$SecondsDelay = 5
    $ps_version = $host.Version.Major
    if ($ps_version -lt 6){
        ignore_cert_error
    	$cmd = {Invoke-WebRequest -UseBasicParsing -uri $resource -Headers $headers }
    }
    else {
    	$cmd = {Invoke-WebRequest -UseBasicParsing -SkipCertificateCheck -uri $resource -Headers $headers -MaximumRetryCount 3 -RetryIntervalSec 3 }
    }

    $retryCount = 0
    $completed = $false
    $response = $null

    while (-not $completed) {
        #$ErrorActionPreference = "Continue"
        try {
            $response = Invoke-Command $cmd
            if ($response.StatusCode -ne 200) {
                throw "Expecting reponse code 200, was: $($response.StatusCode)"
            }
             $completed = $true
        } catch {
            if ($retrycount -ge $Retries) {
                Write-Warning "Request to $url failed the maximum number of $retryCount times."
                throw
            } else {
                Write-Warning "Request to $url failed. Retrying in $SecondsDelay seconds."
                Start-Sleep $SecondsDelay
                $retrycount++
            }
        } 
    }
    return $response | convertFrom-Json
}

Function write_to_file($data, $save_file){
    if ($data.Length -gt 0) {
        try {$write_data = $data | convertTo-Json -Depth 20}
        catch {$write_data = $data}
        $save_file = $save_file + ".json"
        try {[IO.File]::WriteAllLines($save_file, $write_data)}
        catch {$write_data | Out-File -FilePath $save_file}
        }
}

# Start transcription
$ps_version = $host.Version.Major
$ErrorActionPreference="SilentlyContinue"
Stop-Transcript | out-null
$ErrorActionPreference = "Continue"
$now = Get-Date -Format "yyyy.MM.dd"
$save_path = Join-Path -Path $pwd -ChildPath "CB_AC_Data_$now"

# Set up info - remove https and readd it, set headers
$server = $server.Replace("https://", "") 
$server = "https://$server"
$headers = @{
    "X-Auth-Token"= $api_key;
    "Content-Type"= "application/json; charset=utf-8"
    }


# Create a directory to hold the newly created files
write-output "-- Creating new directory to store files: $save_path"
New-Item -Path $pwd -Name "CB_AC_Data_$now" -ItemType "directory" -Force | Out-Null
if ($ps_version -ge 5){
    Start-Transcript -path $save_path\CB_TA_script.log -append
}

# All the static resources we will request from the API
# If adding new, each MUST end with "limit="
$resources = @(
    ("publisher", "/api/bit9platform/v1/publisher?limit=", 0),
    ("computer", "/api/bit9platform/v1/computer?q=daysOffline<32&limit=", 0),
    ("updater", "/api/bit9platform/v1/updater?limit=", 0),
    ("policy", "/api/bit9platform/v1/policy?limit=", 0),
    ("scriptRule", "/api/bit9platform/v1/scriptRule?limit=", 0),
    ("serverPerformance", "/api/bit9platform/v1/serverPerformance?limit=", 0),
    ("trustedDirectory", "/api/bit9platform/v1/trustedDirectory?limit=", 0),
    ("trustedUser", "/api/bit9platform/v1/trustedUser?limit=", 0),
    ("serverConfig", "/api/bit9platform/v1/serverConfig?limit=", 0),
    ("driftReport", "/api/bit9platform/v1/driftReport?limit=", 0),
    ("global_approval_counts", "/api/bit9platform/v1/fileRule?q=sourceType!3&filestate:2&lazyApproval:false&group=datecreated&limit=", 0),
    ("global_approval_counts_2", "/api/bit9platform/v1/fileRule?q=sourceType!3&filestate:2&lazyApproval:false&group=datecreated&grouptype=n&groupstep=1", 0),
    ("td_approval_counts", "/api/bit9platform/v1/fileRule?q=sourceType:2&group=sourceId&limit=", 0),
    ("approval_summary", "/api/bit9platform/v1/fileRule?group=sourceType&limit=", 0),
    ("rule_hits", "/api/bit9platform/v1/event?group=ruleName&limit=", 0),
    ("rapfig_events", "/api/bit9platform/v1/event?q=rapfigName!&q=timestamp>-30d&group=rapfigName&subgroup=RuleName&limit=", 0),
    ("extensions", "/api/bit9platform/v1/fileCatalog?q=dateCreated>-30d&group=fileExtension&limit=", 0),
    ("unapprovedWriters", "/api/bit9platform/v1/event?expand=fileCatalogId&q=subtype:1003&q=fileCatalogId_effectiveState:Unapproved&q=param1:DiscoveredBy[Kernel:Rename]*|DiscoveredBy[Kernel:Create]*|DiscoveredBy[Kernel:Write]*&sort=receivedTimestamp DESC&limit=", 10000),
    ("customRule", "/api/bit9platform/restricted/customRule?limit=", 0),
    ("approvalRequest", "/api/bit9platform/v1/approvalRequest?sort=dateCreated DESC&limit=", 10000),
    ("block_events", "/api/bit9platform/v1/event?q=subtype:801&sort=receivedTimestamp DESC&limit=", 10000),
    ("agent_config", "/api/bit9platform/restricted/agentConfig?limit=", 0),
    ("cache_checks", "/api/bit9platform/v1/event?q=subtype:426&q=timestamp>-30d&limit=", 0),
    ("oldest_event", "/api/bit9platform/v1/event?sort=receivedtimestamp&limit=", 1),
    ("newest_event", "/api/bit9platform/v1/event?sort=receivedtimestamp DESC&limit=", 1),
    ("event_count_30d", "/api/bit9platform/v1/event?q=receivedtimestamp>-30d&limit=", -1),
    ("policy_changes", "/api/bit9platform/v1/event?q=subtype:406&sort=receivedTimestamp DESC&limit=", 10000),
    ("console_logins", "/api/bit9platform/v1/event?q=subtype:300&sort=receivedTimestamp DESC&limit=", 10000),
    ("health_check_events", "/api/bit9platform/v1/event?q=subtype:447&sort=receivedTimestamp DESC&limit=", 10000)
    )

# Removed     ("appTemplate", "/api/bit9platform/restricted/appTemplate?limit=", 0),
# Add requests for the top 4 subtypes & processes to the resources array
$sts_procs = @(
    (
    "top_subtypes", 
    "/api/bit9platform/v1/event?q=subtypeName!&q=timestamp>-30d&group=subtypeName cdesc", 
    "/api/bit9platform/v1/event?q=subtypeName:", 
    "Top 4 Subtypes"
    ),
    (
    "top_processes", 
    "/api/bit9platform/v1/event?q=processFileName!&q=timestamp>-30d&group=processFileName cdesc", 
    "/api/bit9platform/v1/event?q=processFileName:", 
    "Top 4 Processes"
    )
    )
foreach($item in $sts_procs){
    # Get the aggregates for each & write to a file
    Write-Output ("-- Getting " + $item[3])
    $url = $server + $item[1]
    $data = web_request($url)
    $save_file = Join-Path -Path $save_path -ChildPath $item[0]
    write_to_file $data $save_file
    # Add the tops to the resources array
    $top4 = $data | select -First 4
    foreach ($i in $top4){
        $url = $item[2] + $i.Value + "&limit="
        $fn = "tops_" + $i.Value
        $resources += ,@($fn, $url, 10000)
        }
    }

# Get all the data defined in the resources array
foreach($res in $resources){
    write-OutPut ("-- Requesting result count for " + $res[0])
    $save_file = Join-Path -Path $save_path -ChildPath $res[0]
    $url = $server + $res[1] + "-1"
    $avail_items = web_request($url)
    $avail_items = $avail_items.count
    write-OutPut ("   Requesting " + $avail_items + " items for " + $res[0])
    write-OutPut ("   Save file = " + $save_file + ".json")
    
    # Make the requests for the data in chunks of 500
    $all_results = New-Object System.Collections.Generic.List[System.Object]
    $start = 0
    $chunk = "500"
    # Check if we just want one result (1), a count of items (-1), or something more
    if ($res[2] -eq 0){
        $stop = $avail_items
    }
    elseif ($res[2] -eq 1){
        $stop = 1
        $chunk = "1"
    }
    else {
        $stop = ($avail_items, $res[2] | Measure -Min).Minimum
    }
    # The call for just counts (-1) is significanly different than getting actual data
    if ($res[2] -eq -1) {
        $url = $server + $res[1] + "-1"
        $all_results += web_request $url
    }
    else {
        while($start -lt $stop){
            $url = $server + $res[1] + $chunk + "&offset=" + $start
            write-OutPut("   Getting results " + ($start + 1) + " through " + ($avail_items, ($start + 500) | Measure -Min).Minimum)
            $data = web_request $url
            $all_results += $data
            $start += 500
        }
    }
    write_to_file $all_results $save_file
}

# Stop logging here to allow file to be included in the zip
if ($ps_version -ge 5){
    Stop-Transcript
}
$compress = @{
    Path = "$save_path\*"
    CompressionLevel = "Fastest"
    DestinationPath = $save_path + ".zip"
    }
if ($ps_version -gt 4){
    Compress-Archive -Force @compress
    }
