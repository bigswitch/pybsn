# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

## 0.4.0 - UNRELEASED
### Added
 - added optional parameter `params` to all BigDbClient and Node request methods. It allows
   specifying additional query paramters for the BigDB request (e.g., `transaction` or
   `state-type` parameters).
 - added optional parameter `params` to RPC to manually initiate async RPC calls.
   e.g., `initiate-async-id`, `async-id`
### Removed
- python 2 support has been removed.
- python 3.5 support has been removed.
- python 3.6 support is deprecated, and may be removed in the future.
- nosetest has been removed as dependency.

## 0.3.3 - 2021-02-03
### Removed
- `pybsn.bcf`. Pybsn contained a a very partial "Porcelain" API layer called pybsn.bcf. It
  has been removed since it was unused and very incomplete.

### Added
- `pybsn-repl` - optional parameter `-c` allows specifying a non-interactive command to run
  (like ipython).

### Deprecated
- Note: this is the last pybsn version to support python 2. Please upgrade to python 3 if
you want to consume newer pybsn versions.

## 0.3.2 - 2020-04-01
### Added
- `pybsn-repl` - optional parameter `env-token` allows specifying
the name of an environment variable to read the session token from.

## 0.3.1 - 2019-07-01
### Added
- `pybsn.connect` - optional parameter `session_headers` allows specifying
request headers to be included with all requests.

## 0.3.0 - 2019-05-20
### Added 
- Ability to log request/response bodies

### Changed
- Connect API signature to remove unused variable
 
### Fixed 
- Handling of RPCs that don't return data
- Python 2 bug with unicode strings in predicates
- Issue where full schema of RPC was not displayed 

## 0.2.0 - 2019-01-24
### Added
- Support for API tokens

### Changed
- Discovery method for controller scheme and port
