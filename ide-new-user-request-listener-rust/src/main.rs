use std::{
    io::{BufReader, prelude::*},
    net::{TcpListener, TcpStream},
};

use rand::Rng;
use rand::distr::Alphanumeric;
use std::env;

fn main() {
    let port = env::var("NEW_USER_REQUEST_LISTENER_PORT")
        .ok()
        .and_then(|val| val.parse::<i32>().ok())
        .unwrap_or(5123);

    let bind_address = env::var("NEW_USER_REQUEST_BIND_ADDRESS")
        .ok()
        .unwrap_or(String::from("127.0.0.1"));

    println!("Listening on {}:{}", bind_address, port);

    let listener = TcpListener::bind(format!("{bind_address}:{port}")).unwrap();

    for stream in listener.incoming() {
        let stream = stream.unwrap();

        println!("Connection established!");

        handle_connection(stream);
    }
}

fn handle_connection(mut stream: TcpStream) {
    let buf_reader = BufReader::new(&stream);
    let request_line = buf_reader.lines().next().unwrap().unwrap();

    if !request_line.contains("GET /new-username") {
        println!("Wrong url. Should hit /new-username");

        let status_line = "HTTP/1.1 400 Bad Request";
        let contents = "Did you mean to hit /new-username instead?";
        let length = contents.len();
        let content_length_header = format!("Content-Length: {length}");
        let response = format!("{status_line}\r\n{content_length_header}\r\n\r\n{contents}");
        stream.write_all(response.as_bytes()).unwrap();
    } else {
        println!("Generating random username");

        let mut rng = rand::rng();

        let mut username: String = (&mut rng)
            .sample_iter(Alphanumeric)
            .take(13)
            .map(char::from)
            .collect();

        username = username.to_lowercase();

        println!("Generated username {}", username);

        let status_line = "HTTP/1.1 200 OK";
        let contents = format!("{{\"username\": \"{username}\"}}");
        let length = contents.len();
        let content_length_header = format!("Content-Length: {length}");
        let content_type_header = "Content-Type: application/json";
        let response = format!(
            "{status_line}\r\n{content_length_header}\r\n{content_type_header}\r\n\r\n{contents}"
        );
        stream.write_all(response.as_bytes()).unwrap();
    }
}
