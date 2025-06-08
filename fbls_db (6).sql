-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 14, 2025 at 04:35 AM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `fbls_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `borrowers`
--

CREATE TABLE `borrowers` (
  `id` int(11) NOT NULL,
  `equipment_id` int(11) NOT NULL,
  `borrower_name` varchar(100) NOT NULL,
  `room_number` varchar(100) NOT NULL,
  `contact_number` varchar(20) DEFAULT NULL,
  `borrow_date` timestamp NOT NULL DEFAULT current_timestamp(),
  `expected_return_date` datetime NOT NULL,
  `actual_return_date` datetime DEFAULT NULL,
  `status` enum('pending','approved','rejected','returned') DEFAULT 'pending',
  `remarks` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `reminder_sent` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `borrowers`
--

INSERT INTO `borrowers` (`id`, `equipment_id`, `borrower_name`, `room_number`, `contact_number`, `borrow_date`, `expected_return_date`, `actual_return_date`, `status`, `remarks`, `created_at`, `reminder_sent`) VALUES
(93, 2, 'Filmarkerz', 'IECS room 21', '0912312', '2025-05-14 02:24:17', '2025-05-30 10:24:00', '2025-05-14 10:24:20', 'returned', NULL, '2025-05-14 02:24:17', 0),
(94, 5, 'Filmark', 'IECS room 21', '0912312', '2025-05-14 02:30:58', '2025-05-16 10:30:00', '2025-05-14 10:31:02', 'returned', NULL, '2025-05-14 02:30:58', 0);

-- --------------------------------------------------------

--
-- Table structure for table `equipment`
--

CREATE TABLE `equipment` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `category` varchar(50) NOT NULL,
  `status` enum('available','borrowed','maintenance') DEFAULT 'available',
  `serial_number` varchar(50) DEFAULT NULL,
  `image_path` varchar(255) DEFAULT NULL,
  `condition_notes` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `equipment`
--

INSERT INTO `equipment` (`id`, `name`, `category`, `status`, `serial_number`, `image_path`, `condition_notes`, `created_at`) VALUES
(1, 'EPSON EB-X500 Projector', 'Projector', 'borrowed', 'PRJ-001', 'images/20250216_171603_EPSON_EB-X500_Projector.jpg', 'Good condition, recently serviced ', '2025-02-15 01:49:35'),
(2, 'BenQ MS550 Projector', 'Projector', 'available', 'PRJ-002', 'images/20250216_171613_BenQ_MS550_Projector.jpg', 'New unit, purchased 2024', '2025-02-15 01:49:35'),
(3, 'Industrial Stand Fan 20\"', 'Fan', 'available', 'FAN-001', 'images/20250216_171624_Industrial_Stand_Fan_20.jpg', 'Working properly, cleaned regularly yes', '2025-02-15 01:49:35'),
(4, 'Tornado Stand Fan 16\"', 'Fan', 'available', 'FAN-002', 'images/20250216_171640_Tornado_Stand_Fan_16.jpg', 'Good condition, minor scratches', '2025-02-15 01:49:35'),
(5, 'Heavy Duty Extension Wire 30m', 'Extension', 'available', 'EXT-001', 'images/20250216_171650_Heavy_Duty_Extension_Wire_30m.jpg', 'New condition, industrial grade', '2025-02-15 01:49:35'),
(26, 'bread', 'Projector', 'available', 'test11', 'images/20250227_173837_pngwing.com_13.png', 'bread', '2025-02-27 09:38:37'),
(27, 'pandesal', 'Projector', 'available', 'pandesal', 'images/20250503_143914_pexels-felixmittermeier-957040.jpg', 'pan', '2025-03-01 03:44:13'),
(28, 'TEST', 'Projector', 'available', 'test111', 'images/20250422_225524_466874208_560408323352082_205202596750541408_n.jpg', 'asd', '2025-04-22 14:55:24');

-- --------------------------------------------------------

--
-- Table structure for table `faculty`
--

CREATE TABLE `faculty` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `department` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `status` enum('active','inactive') DEFAULT 'active'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `faculty`
--

INSERT INTO `faculty` (`id`, `name`, `email`, `password`, `department`, `created_at`, `status`) VALUES
(1, 'Elyndor', 'Elyndor@gmail.com', 'scrypt:32768:8:1$YcjxmgwSuuZit7PQ$0c01b149cafd33656acc4bd027f2742a552db22b2074ddea7eab074e7f860c21b502941d3b02b7bc8ea6731db502e8a6d827f40cac643a49b53f44df936a0a5b', 'IECS', '2025-02-15 01:40:20', 'active'),
(2, 'test', 'test@gmail.com', 'scrypt:32768:8:1$iydD0cCqLzCn7Lt4$bb4f2ee186b8f535dbab19cf962753a02ff9daba9f046134ed0031cb3895e46a215be5c8e51f9c0cbc0e6ef6e0ad68c15bd8ef89a62753aced9d594144882a54', 'IECS', '2025-02-16 06:42:52', 'active'),
(3, 'dodong', 'Dodong@gmail.com', 'scrypt:32768:8:1$JHBan2XmrVKqVcCN$2020fc4d835596141d386239a5d418bf35988fbd48dc5a1321c6f78a96f0bcbd9e66099dd9df064d9aa0680ce63a912e8cce8625d2ebc787359f399d52dd2dab', 'IECS', '2025-02-26 04:52:57', 'active'),
(4, 'dodong', 'dodong2@gmail.com', 'scrypt:32768:8:1$DsdhTYldlYiNxrCs$bbcde8ed0a67a5c3fd6cca9167c5ff3e06b9de87b329b6e4797bd8804ef83499bc6ccb815699352190cb903dab422e8bb9871505448af49c4e2f1f5ed2e726c7', 'IECS', '2025-02-26 10:24:36', 'active'),
(5, 'pandesal', 'pandesal@gmail.com', 'scrypt:32768:8:1$kTdRmSXIzr2iZiZq$0b307ed49da3ca9d709f6bec152902d739fa228b6e2c4a6caed8ba41186eb7ca143a1407c72a0e77ad29abe2322e03654b9a92226773b9c20fd9266f2a92e7a4', 'IECS', '2025-02-28 09:37:10', 'active');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `borrowers`
--
ALTER TABLE `borrowers`
  ADD PRIMARY KEY (`id`),
  ADD KEY `equipment_id` (`equipment_id`),
  ADD KEY `idx_status` (`status`);

--
-- Indexes for table `equipment`
--
ALTER TABLE `equipment`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `serial_number` (`serial_number`);

--
-- Indexes for table `faculty`
--
ALTER TABLE `faculty`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `borrowers`
--
ALTER TABLE `borrowers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=95;

--
-- AUTO_INCREMENT for table `equipment`
--
ALTER TABLE `equipment`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=29;

--
-- AUTO_INCREMENT for table `faculty`
--
ALTER TABLE `faculty`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `borrowers`
--
ALTER TABLE `borrowers`
  ADD CONSTRAINT `borrowers_ibfk_1` FOREIGN KEY (`equipment_id`) REFERENCES `equipment` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
