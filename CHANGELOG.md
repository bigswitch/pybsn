# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

## 0.3.2 - 04-01-2020
### Added
- `pybsn-repl` - optional parameter `env-token` allows specifying
the name of an environment variable to read the session token from.

## 0.3.1 - 07-01-2019
### Added
- `pybsn.connect` - optional parameter `session_headers` allows specifying
request headers to be included with all requests.

## 0.3.0 - 5-20-2019
### Added 
- Ability to log request/response bodies

### Changed
- Connect API signature to remove unused variable
 
### Fixed 
- Handling of RPCs that don't return data
- Python 2 bug with unicode strings in predicates
- Issue where full schema of RPC was not displayed 

## 0.2.0 - 1-24-2019
### Added
- Support for API tokens

### Changed
- Discovery method for controller scheme and port
