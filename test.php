<?php

$_SERVER['SERVER_NAME'] = 'test' . rand(0, 1000) . '.com';

require("l8.php");

l8::debug("Testing - D", ['test' => 1, 'testing' => [2,3]]);
l8::error("Testing - E this is a long message, seeing that things wrap to multiple lines correctly. blah blah blah blah blah blah", ['test' => 1, 'testing' => [2,3]]);


for ($i = 0; $i < 100; $i++) {
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
    l8::info("Testing - $i", ['test' => $i++]);
}