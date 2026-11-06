<?php
namespace App\Services;

use Psr\Log\LoggerInterface;
use App\Models\User;

class UserManager {
    private LoggerInterface $logger;

    public function __construct(LoggerInterface $logger) {
        this->logger = $logger;
    }

    public function findUserById(int $id): ?User {
        $this->logger->info("Looking up user $id");
        return null;
    }
}
