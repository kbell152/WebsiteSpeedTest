<?php
/*
 * This file is not used by the local repo or CLI app.
 * It is kept here only to track website changes.
 * Upload it to the website for any changes here to take effect.
 */
$reportsDir = __DIR__ . "/reports";
$reports = [];

if (is_dir($reportsDir)) {
    foreach (glob($reportsDir . "/*.html") as $file) {
        $name = basename($file);
        preg_match('/(\d{8})-(\d{6})/', $name, $matches);

if ($matches) {
    $date = $matches[1];
    $timePart = $matches[2];

    $year  = substr($date,0,4);
    $month = substr($date,4,2);
    $day   = substr($date,6,2);

    $hour  = substr($timePart,0,2);
    $min   = substr($timePart,2,2);
    $sec   = substr($timePart,4,2);

    $time = strtotime("$year-$month-$day $hour:$min:$sec");
} else {
    $time = filemtime($file);
}

        $type = "Report";
        if (stripos($name, "mobile") !== false) $type = "Mobile";
        if (stripos($name, "desktop") !== false) $type = "Desktop";

        $reports[] = [
            "name" => $name,
            "time" => $time,
            "time_display" => date("Y-m-d h:i A", $time),
            "type" => $type,
            "url" => "reports/" . $name,
        ];
    }
}

usort($reports, function($a, $b) {
    return $b["time"] <=> $a["time"];
});

$reports = array_slice($reports, 0, 5);
?>

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>WebPerf Reports</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background: #f4f6f9;
        }
        h1 {
            margin-bottom: 30px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            background: white;
        }
        th, td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }
        th {
            background: #333;
            color: white;
        }
        a {
            color: #1a73e8;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>

<h1>Website Performance Reports</h1>

<table>
    <tr>
        <th>Last Updated</th>
        <th>Type</th>
        <th>Report</th>
    </tr>

    <?php if (count($reports) === 0): ?>
        <tr>
            <td colspan="3">No reports uploaded yet.</td>
        </tr>
    <?php else: ?>
        <?php foreach ($reports as $report): ?>
            <tr>
                <td><?php echo htmlspecialchars($report["time_display"]); ?></td>
                <td><?php echo htmlspecialchars($report["type"]); ?></td>
                <td>
                    <a href="<?php echo htmlspecialchars($report["url"]); ?>" target="_blank" rel="noopener noreferrer">
                        <?php echo htmlspecialchars($report["name"]); ?>
                    </a>
                </td>
            </tr>
        <?php endforeach; ?>
    <?php endif; ?>
</table>

</body>
</html>
