param(
    [switch]$Docker
)

if ($Docker) {
    python start.py --docker
} else {
    python start.py $args
}
