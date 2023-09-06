-- SPDX-FileCopyrightText: 2023 2023 The WESkit Team
--
-- SPDX-License-Identifier: MIT

-- MySQL dump 10.13  Distrib 8.0.23, for Linux (x86_64)
--
-- Host: localhost    Database: keycloak
-- ------------------------------------------------------
-- Server version	8.0.23

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `keycloak`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `keycloak` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `keycloak`;

--
-- Table structure for table `ADMIN_EVENT_ENTITY`
--

DROP TABLE IF EXISTS `ADMIN_EVENT_ENTITY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ADMIN_EVENT_ENTITY` (
  `ID` varchar(36) NOT NULL,
  `ADMIN_EVENT_TIME` bigint DEFAULT NULL,
  `REALM_ID` varchar(255) DEFAULT NULL,
  `OPERATION_TYPE` varchar(255) DEFAULT NULL,
  `AUTH_REALM_ID` varchar(255) DEFAULT NULL,
  `AUTH_CLIENT_ID` varchar(255) DEFAULT NULL,
  `AUTH_USER_ID` varchar(255) DEFAULT NULL,
  `IP_ADDRESS` varchar(255) DEFAULT NULL,
  `RESOURCE_PATH` text,
  `REPRESENTATION` text,
  `ERROR` varchar(255) DEFAULT NULL,
  `RESOURCE_TYPE` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ADMIN_EVENT_ENTITY`
--

LOCK TABLES `ADMIN_EVENT_ENTITY` WRITE;
/*!40000 ALTER TABLE `ADMIN_EVENT_ENTITY` DISABLE KEYS */;
/*!40000 ALTER TABLE `ADMIN_EVENT_ENTITY` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ASSOCIATED_POLICY`
--

DROP TABLE IF EXISTS `ASSOCIATED_POLICY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ASSOCIATED_POLICY` (
  `POLICY_ID` varchar(36) NOT NULL,
  `ASSOCIATED_POLICY_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`POLICY_ID`,`ASSOCIATED_POLICY_ID`),
  KEY `IDX_ASSOC_POL_ASSOC_POL_ID` (`ASSOCIATED_POLICY_ID`),
  CONSTRAINT `FK_FRSR5S213XCX4WNKOG82SSRFY` FOREIGN KEY (`ASSOCIATED_POLICY_ID`) REFERENCES `RESOURCE_SERVER_POLICY` (`ID`),
  CONSTRAINT `FK_FRSRPAS14XCX4WNKOG82SSRFY` FOREIGN KEY (`POLICY_ID`) REFERENCES `RESOURCE_SERVER_POLICY` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ASSOCIATED_POLICY`
--

LOCK TABLES `ASSOCIATED_POLICY` WRITE;
/*!40000 ALTER TABLE `ASSOCIATED_POLICY` DISABLE KEYS */;
/*!40000 ALTER TABLE `ASSOCIATED_POLICY` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `AUTHENTICATION_EXECUTION`
--

DROP TABLE IF EXISTS `AUTHENTICATION_EXECUTION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `AUTHENTICATION_EXECUTION` (
  `ID` varchar(36) NOT NULL,
  `ALIAS` varchar(255) DEFAULT NULL,
  `AUTHENTICATOR` varchar(36) DEFAULT NULL,
  `REALM_ID` varchar(36) DEFAULT NULL,
  `FLOW_ID` varchar(36) DEFAULT NULL,
  `REQUIREMENT` int DEFAULT NULL,
  `PRIORITY` int DEFAULT NULL,
  `AUTHENTICATOR_FLOW` bit(1) NOT NULL DEFAULT b'0',
  `AUTH_FLOW_ID` varchar(36) DEFAULT NULL,
  `AUTH_CONFIG` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_AUTH_EXEC_REALM_FLOW` (`REALM_ID`,`FLOW_ID`),
  KEY `IDX_AUTH_EXEC_FLOW` (`FLOW_ID`),
  CONSTRAINT `FK_AUTH_EXEC_FLOW` FOREIGN KEY (`FLOW_ID`) REFERENCES `AUTHENTICATION_FLOW` (`ID`),
  CONSTRAINT `FK_AUTH_EXEC_REALM` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AUTHENTICATION_EXECUTION`
--

LOCK TABLES `AUTHENTICATION_EXECUTION` WRITE;
/*!40000 ALTER TABLE `AUTHENTICATION_EXECUTION` DISABLE KEYS */;
INSERT INTO `AUTHENTICATION_EXECUTION` VALUES ('010e1a35-b8c9-4490-9430-7bdf271646e5',NULL,'idp-username-password-form','master','31a3c0f0-8aca-4afc-841a-da50e4f6b27d',0,10,_binary '\0',NULL,NULL),('04120a62-6980-44ee-8382-04715d98415f',NULL,NULL,'WESkit','fe42a8d7-5e5c-4014-9ec3-6d7de645d5e8',1,20,_binary '','2cf706ee-8d84-4ed2-ad89-8e78ac2a0a69',NULL),('042e31ab-b068-4c36-868f-eb68936b426b',NULL,NULL,'master','746697f7-ec22-4046-948d-3a3518c6f26e',0,20,_binary '','de5332d3-90ee-4b9c-91c9-6a59a5d3d49b',NULL),('0546ade5-ea4d-4952-8106-8ad701f454cb',NULL,'registration-page-form','master','ef6ff606-c66a-4b1d-801c-e966c33c1b2a',0,10,_binary '','6126faa5-8c83-444b-acb3-3027c7de6f97',NULL),('0a536e2d-bad3-49aa-bd68-6b9f72359daf',NULL,'idp-confirm-link','WESkit','a23902f0-020d-4487-b3b9-b7ac39d5d066',0,10,_binary '\0',NULL,NULL),('0b21dec8-733c-4180-a1cd-dc818de60f91',NULL,'direct-grant-validate-password','WESkit','88aea7e1-06d3-48a2-bc87-2b0bee543f11',0,20,_binary '\0',NULL,NULL),('0f26264b-3926-46b4-be70-ba0f285b4843',NULL,NULL,'master','9a9bfc27-6607-4f49-b011-6030c2f87f7f',0,20,_binary '','6e1a87bb-5fe8-45fc-b175-8876fd0fd500',NULL),('108d7f8e-f55e-47d7-b111-05b0f4ec18d3',NULL,'conditional-user-configured','WESkit','2cf706ee-8d84-4ed2-ad89-8e78ac2a0a69',0,10,_binary '\0',NULL,NULL),('110671d3-f0f0-43a4-86ae-f5035357fe65',NULL,'auth-otp-form','WESkit','5f18bce2-ab51-4cc3-a574-8884c36c39db',0,20,_binary '\0',NULL,NULL),('134d4796-d0c5-412d-9c0e-106c2424b370',NULL,'auth-cookie','master','c0344e9e-b3cd-4468-9248-3fb84023a775',2,10,_binary '\0',NULL,NULL),('23931258-6968-4b9b-ac3b-9de4c1eb4e1d',NULL,NULL,'WESkit','88aea7e1-06d3-48a2-bc87-2b0bee543f11',1,30,_binary '','c5ebe06f-1f65-41d9-bec0-9343c4eb9328',NULL),('28d67b84-f4fa-4dbe-aa40-8834fda25693',NULL,'auth-otp-form','master','e3c65014-8f6d-4699-bd0f-5a60d857c1bf',0,20,_binary '\0',NULL,NULL),('2a419769-d4b4-41ac-a609-68093bb140ff',NULL,'registration-password-action','master','6126faa5-8c83-444b-acb3-3027c7de6f97',0,50,_binary '\0',NULL,NULL),('30060a65-24e8-4427-9b58-e32a97b5f4e1',NULL,'reset-otp','master','8e0430ce-ae65-4506-8fde-7ee28810407a',0,20,_binary '\0',NULL,NULL),('471db918-9e30-4967-93f1-7270f41f1a7a',NULL,'auth-otp-form','WESkit','2cf706ee-8d84-4ed2-ad89-8e78ac2a0a69',0,20,_binary '\0',NULL,NULL),('4863f1ec-8c3b-43fe-8c18-a81e85388554',NULL,'conditional-user-configured','master','8e0430ce-ae65-4506-8fde-7ee28810407a',0,10,_binary '\0',NULL,NULL),('501d6da1-02d6-4cf3-a4f7-259c6ce706f7',NULL,'reset-password','master','d04b00e9-0d38-42cf-b01e-bb1186506485',0,30,_binary '\0',NULL,NULL),('51ff46cb-ac72-43c9-af76-ffbb0e39e26e',NULL,'basic-auth-otp','master','6e1a87bb-5fe8-45fc-b175-8876fd0fd500',3,20,_binary '\0',NULL,NULL),('56ead476-131d-4af1-a5a8-b6b75fdd75cc',NULL,'docker-http-basic-authenticator','master','4ab909dd-030d-43a1-a69f-ce975803d511',0,10,_binary '\0',NULL,NULL),('5c36c805-3b1b-4828-b8fc-38884995222b',NULL,'conditional-user-configured','WESkit','5f18bce2-ab51-4cc3-a574-8884c36c39db',0,10,_binary '\0',NULL,NULL),('5c618da2-a794-4d02-b45f-f05ccae609f8',NULL,'client-secret-jwt','WESkit','6ad3a3f0-62ca-45cc-a0e8-593e58c987c0',2,30,_binary '\0',NULL,NULL),('5f522c2d-cdab-429b-8141-78740aae320a',NULL,'basic-auth','WESkit','6d4b0963-75e8-4135-9e58-010a4ce602b7',0,10,_binary '\0',NULL,NULL),('5fa1fe8b-ff6f-4fa1-b220-fcc114540601',NULL,'client-jwt','master','92431b5a-91d0-4389-bb3e-2f5b3b4aee59',2,20,_binary '\0',NULL,NULL),('604049f3-3d2c-4a49-b57c-0a95613c0558',NULL,'idp-create-user-if-unique','master','9d2106cf-7b6d-4462-96f0-d177e4a454b6',2,10,_binary '\0',NULL,'205ebd4b-8a3f-4584-a985-624c3e91e6e4'),('63ff37a8-ca55-4f63-bb28-965e94df2f91',NULL,'no-cookie-redirect','master','9a9bfc27-6607-4f49-b011-6030c2f87f7f',0,10,_binary '\0',NULL,NULL),('646c3a02-97bb-470a-b9d1-0358378b3d78',NULL,'auth-spnego','master','c0344e9e-b3cd-4468-9248-3fb84023a775',3,20,_binary '\0',NULL,NULL),('6ad696f7-ffcd-4393-9f71-2c39950837e6',NULL,'client-x509','WESkit','6ad3a3f0-62ca-45cc-a0e8-593e58c987c0',2,40,_binary '\0',NULL,NULL),('6c0b6efe-7299-410b-b848-bcb595cbaf62',NULL,NULL,'WESkit','c1e93565-0e36-457b-b3e6-eff165c3e862',1,20,_binary '','5f18bce2-ab51-4cc3-a574-8884c36c39db',NULL),('6ef65f50-9681-4ff1-aec3-729ae93b33a5',NULL,NULL,'WESkit','ec4b4658-10f3-40f5-9b0c-54d76f7c5d9b',0,20,_binary '','6d4b0963-75e8-4135-9e58-010a4ce602b7',NULL),('6f1248d3-fed0-4355-958f-51a016ac006d',NULL,'client-secret','master','92431b5a-91d0-4389-bb3e-2f5b3b4aee59',2,10,_binary '\0',NULL,NULL),('7b9eab1e-f12d-49e1-ad6a-772ed397d789',NULL,'identity-provider-redirector','WESkit','92ed5a7a-96ae-4cb9-b56d-eb20a9dffcbb',2,25,_binary '\0',NULL,NULL),('7ba96761-78af-45c8-9575-0ab565f1b41a',NULL,NULL,'master','9d2106cf-7b6d-4462-96f0-d177e4a454b6',2,20,_binary '','746697f7-ec22-4046-948d-3a3518c6f26e',NULL),('7e6e4c34-7797-4fe8-9dc2-8c7fa7e29d47',NULL,'direct-grant-validate-username','WESkit','88aea7e1-06d3-48a2-bc87-2b0bee543f11',0,10,_binary '\0',NULL,NULL),('8267b911-cf05-4f63-a7c6-2e4d04d66200',NULL,'basic-auth-otp','WESkit','6d4b0963-75e8-4135-9e58-010a4ce602b7',3,20,_binary '\0',NULL,NULL),('84937977-a668-4f1e-aa4d-715ee744f981',NULL,'registration-page-form','WESkit','93343dd1-d31e-4814-a76b-0ef0f214fd2c',0,10,_binary '','f992dda7-3464-42c3-8c9d-0d755f02a984',NULL),('84eba53e-a47b-4c08-bdd4-0cea9732c172',NULL,'registration-profile-action','master','6126faa5-8c83-444b-acb3-3027c7de6f97',0,40,_binary '\0',NULL,NULL),('884d9728-5ccd-449f-9944-6d0ae0ae9ff0',NULL,'conditional-user-configured','WESkit','c5ebe06f-1f65-41d9-bec0-9343c4eb9328',0,10,_binary '\0',NULL,NULL),('8b698848-03d7-4853-a69a-0c60f496b4df',NULL,'basic-auth','master','6e1a87bb-5fe8-45fc-b175-8876fd0fd500',0,10,_binary '\0',NULL,NULL),('8bbc4fae-6f0b-42eb-866b-dfb98539cbd3',NULL,'direct-grant-validate-otp','WESkit','c5ebe06f-1f65-41d9-bec0-9343c4eb9328',0,20,_binary '\0',NULL,NULL),('8dc4db65-1ad9-4cdc-bdef-172be3e583be',NULL,'client-x509','master','92431b5a-91d0-4389-bb3e-2f5b3b4aee59',2,40,_binary '\0',NULL,NULL),('8fcaf255-0585-4f46-b0a9-4251775c8780',NULL,'identity-provider-redirector','master','c0344e9e-b3cd-4468-9248-3fb84023a775',2,25,_binary '\0',NULL,NULL),('905ee48a-49b5-4b3f-b9e8-e5ead37a514a',NULL,'reset-otp','WESkit','15841c4a-5579-46ad-9d29-db3c94df4ab7',0,20,_binary '\0',NULL,NULL),('9081f7b9-3ddb-43df-8be6-ef46eeea78c2',NULL,'auth-cookie','WESkit','92ed5a7a-96ae-4cb9-b56d-eb20a9dffcbb',2,10,_binary '\0',NULL,NULL),('92273031-645c-4699-939d-dc950caf65f5',NULL,'reset-credentials-choose-user','WESkit','51f3e5bf-c65b-4e46-8c25-6bd8f6a4c155',0,10,_binary '\0',NULL,NULL),('996a2369-6065-4e64-8bd2-c293219ed0f2',NULL,NULL,'WESkit','d4f89522-a21d-4eca-9b27-e8ce91cc5694',0,20,_binary '','8a00905d-0bac-4319-924b-b75ec71bc8b8',NULL),('9c6074bd-068a-4fec-95cb-64af1982344f',NULL,NULL,'master','b6f30b8f-0340-4d9b-9c69-7930569063da',0,20,_binary '','9d2106cf-7b6d-4462-96f0-d177e4a454b6',NULL),('9e9d9707-9cb2-493f-8cee-7eefee70ec42',NULL,'auth-otp-form','master','1303b5e1-1f22-4599-b327-b25ef4392aff',0,20,_binary '\0',NULL,NULL),('a16b4416-443a-40bd-8568-e5d7524cb320',NULL,'client-secret-jwt','master','92431b5a-91d0-4389-bb3e-2f5b3b4aee59',2,30,_binary '\0',NULL,NULL),('a471aa07-2d80-4138-8dd8-19c6daf4524e',NULL,NULL,'WESkit','51f3e5bf-c65b-4e46-8c25-6bd8f6a4c155',1,40,_binary '','15841c4a-5579-46ad-9d29-db3c94df4ab7',NULL),('a64bcdf0-de9b-4c44-8410-440d5fef983b',NULL,'client-secret','WESkit','6ad3a3f0-62ca-45cc-a0e8-593e58c987c0',2,10,_binary '\0',NULL,NULL),('a9f3a30e-8f82-4c1a-81ec-16b1bf062a29',NULL,'idp-create-user-if-unique','WESkit','8a00905d-0bac-4319-924b-b75ec71bc8b8',2,10,_binary '\0',NULL,'543f7589-961a-42cb-a419-5b4f9213b92b'),('ac64faf1-360f-4860-b4e7-14c5f2d9955b',NULL,'http-basic-authenticator','WESkit','bdd3adf6-08f7-466b-89b7-a8be23e23614',0,10,_binary '\0',NULL,NULL),('ad31d83b-de73-45e2-b0de-f7d18409f68d',NULL,NULL,'master','de5332d3-90ee-4b9c-91c9-6a59a5d3d49b',2,20,_binary '','31a3c0f0-8aca-4afc-841a-da50e4f6b27d',NULL),('ae5e4419-4099-48d7-b18f-8ba425b72a0a',NULL,'auth-spnego','WESkit','92ed5a7a-96ae-4cb9-b56d-eb20a9dffcbb',3,20,_binary '\0',NULL,NULL),('b4171dba-b1a4-44dd-a15f-0e1b8973e729',NULL,NULL,'WESkit','a23902f0-020d-4487-b3b9-b7ac39d5d066',0,20,_binary '','d4604f2f-8c94-4498-a548-621aed46af34',NULL),('b8a504f2-96cf-4ca3-a4ae-3a4f304f012c',NULL,NULL,'master','d04b00e9-0d38-42cf-b01e-bb1186506485',1,40,_binary '','8e0430ce-ae65-4506-8fde-7ee28810407a',NULL),('b9526eca-9bb8-4244-8baf-7bd9265098d3',NULL,NULL,'master','08d6c5ff-abc4-4d65-b9fc-e3372d62fcc0',1,30,_binary '','81d48717-e21f-425a-9232-7a11c63bd5b1',NULL),('bab9261d-631c-4a93-b506-a661f2006dbd',NULL,'direct-grant-validate-otp','master','81d48717-e21f-425a-9232-7a11c63bd5b1',0,20,_binary '\0',NULL,NULL),('bd8221e1-a7d5-4672-899c-488a489ec30e',NULL,'conditional-user-configured','WESkit','15841c4a-5579-46ad-9d29-db3c94df4ab7',0,10,_binary '\0',NULL,NULL),('bda2dfb1-91c1-48cb-99f4-6644d41e1a1b',NULL,'auth-spnego','master','6e1a87bb-5fe8-45fc-b175-8876fd0fd500',3,30,_binary '\0',NULL,NULL),('c2ac42c8-1638-4cd5-b0e2-85bb6911d5c2',NULL,'direct-grant-validate-username','master','08d6c5ff-abc4-4d65-b9fc-e3372d62fcc0',0,10,_binary '\0',NULL,NULL),('c32295cd-37ce-4a12-8379-0bed209ed357',NULL,'registration-recaptcha-action','master','6126faa5-8c83-444b-acb3-3027c7de6f97',3,60,_binary '\0',NULL,NULL),('c4ab6192-fdaa-49ec-8efe-df9fec8e963d',NULL,'idp-confirm-link','master','746697f7-ec22-4046-948d-3a3518c6f26e',0,10,_binary '\0',NULL,NULL),('c4b9e0da-0627-4da2-9f46-cdc175a44c0f',NULL,'auth-spnego','WESkit','6d4b0963-75e8-4135-9e58-010a4ce602b7',3,30,_binary '\0',NULL,NULL),('c4ebda03-9b3d-4234-9db9-03cbc4d87a5b',NULL,'idp-review-profile','master','b6f30b8f-0340-4d9b-9c69-7930569063da',0,10,_binary '\0',NULL,'7ac056f1-c0b1-4f39-8076-eaedd1262a2a'),('c5aef1d8-2a19-4e8d-b4d3-fa734145a1b2',NULL,NULL,'master','84399049-7a8f-41cd-93f2-ac5c275403fa',1,20,_binary '','1303b5e1-1f22-4599-b327-b25ef4392aff',NULL),('c7691929-854d-4c26-ae5b-ac3928a91614',NULL,'idp-username-password-form','WESkit','fe42a8d7-5e5c-4014-9ec3-6d7de645d5e8',0,10,_binary '\0',NULL,NULL),('c7d0cd16-25f9-4f96-a7e0-4d1ad87c326d',NULL,'conditional-user-configured','master','1303b5e1-1f22-4599-b327-b25ef4392aff',0,10,_binary '\0',NULL,NULL),('c7d9d3fe-cfa4-45f3-83f5-f971cfdebfe9',NULL,'reset-credentials-choose-user','master','d04b00e9-0d38-42cf-b01e-bb1186506485',0,10,_binary '\0',NULL,NULL),('c8d90d6b-6bd7-4849-9075-0bc868ad1726',NULL,'conditional-user-configured','master','e3c65014-8f6d-4699-bd0f-5a60d857c1bf',0,10,_binary '\0',NULL,NULL),('c9d75106-6d91-459d-876a-b90c44e13b85',NULL,'auth-username-password-form','master','84399049-7a8f-41cd-93f2-ac5c275403fa',0,10,_binary '\0',NULL,NULL),('cb5cdf73-c064-43f7-baf2-8c0e0bdadde7',NULL,'client-jwt','WESkit','6ad3a3f0-62ca-45cc-a0e8-593e58c987c0',2,20,_binary '\0',NULL,NULL),('cf4c761b-3f01-4108-b58b-adb77b80449a',NULL,'direct-grant-validate-password','master','08d6c5ff-abc4-4d65-b9fc-e3372d62fcc0',0,20,_binary '\0',NULL,NULL),('d1cac123-22f1-4be1-a634-773d2db659d8',NULL,'conditional-user-configured','master','81d48717-e21f-425a-9232-7a11c63bd5b1',0,10,_binary '\0',NULL,NULL),('d1dc9b71-ab7b-41ad-82f9-f9d37fec3f12',NULL,'idp-review-profile','WESkit','d4f89522-a21d-4eca-9b27-e8ce91cc5694',0,10,_binary '\0',NULL,'7b4273a8-b9a7-45f9-ab16-56c496143f28'),('d2f367f2-12a7-4184-abba-48c717baada9',NULL,'reset-credential-email','master','d04b00e9-0d38-42cf-b01e-bb1186506485',0,20,_binary '\0',NULL,NULL),('d63d0354-f491-4865-ab46-c4d7a50e2315',NULL,'no-cookie-redirect','WESkit','ec4b4658-10f3-40f5-9b0c-54d76f7c5d9b',0,10,_binary '\0',NULL,NULL),('d846e222-24e2-419b-8875-c4de6d5a3179',NULL,'reset-password','WESkit','51f3e5bf-c65b-4e46-8c25-6bd8f6a4c155',0,30,_binary '\0',NULL,NULL),('d8b69e42-d3b9-4f9f-a0b4-13a91c83e5eb',NULL,NULL,'master','c0344e9e-b3cd-4468-9248-3fb84023a775',2,30,_binary '','84399049-7a8f-41cd-93f2-ac5c275403fa',NULL),('e20030a0-295d-43b1-9d14-41a1a971e2da',NULL,NULL,'WESkit','d4604f2f-8c94-4498-a548-621aed46af34',2,20,_binary '','fe42a8d7-5e5c-4014-9ec3-6d7de645d5e8',NULL),('e5731bdb-f933-4554-9a0e-ea77b0eb14bf',NULL,'registration-recaptcha-action','WESkit','f992dda7-3464-42c3-8c9d-0d755f02a984',3,60,_binary '\0',NULL,NULL),('e96ed489-10ff-43e9-a7a9-9aef7a0799b8',NULL,'idp-email-verification','master','de5332d3-90ee-4b9c-91c9-6a59a5d3d49b',2,10,_binary '\0',NULL,NULL),('eaf16f43-a084-4bbe-8089-f7aaac5ffee1',NULL,'registration-profile-action','WESkit','f992dda7-3464-42c3-8c9d-0d755f02a984',0,40,_binary '\0',NULL,NULL),('ebc9b7cb-9079-4d50-bb00-b6e2c1fa24e7',NULL,NULL,'master','31a3c0f0-8aca-4afc-841a-da50e4f6b27d',1,20,_binary '','e3c65014-8f6d-4699-bd0f-5a60d857c1bf',NULL),('ee4bfc48-90c1-463e-9611-5926ad7fa2d7',NULL,'http-basic-authenticator','master','178fbc31-cee8-4209-b189-79404bc1ece4',0,10,_binary '\0',NULL,NULL),('eed7fbf6-27e2-4113-b30d-a3417372dc81',NULL,'auth-username-password-form','WESkit','c1e93565-0e36-457b-b3e6-eff165c3e862',0,10,_binary '\0',NULL,NULL),('ef3eb1da-c535-493d-b185-ad1e4bf0f38e',NULL,'docker-http-basic-authenticator','WESkit','30d3b23c-fb6d-41e0-afd8-f11714a972cb',0,10,_binary '\0',NULL,NULL),('f242d58d-48ee-4058-bcc5-49abc9553788',NULL,'idp-email-verification','WESkit','d4604f2f-8c94-4498-a548-621aed46af34',2,10,_binary '\0',NULL,NULL),('f36e5935-8c8b-4239-ba28-994bc6392fa8',NULL,NULL,'WESkit','92ed5a7a-96ae-4cb9-b56d-eb20a9dffcbb',2,30,_binary '','c1e93565-0e36-457b-b3e6-eff165c3e862',NULL),('f7441726-7a9f-4b6e-8b3d-ae4f5778e7cc',NULL,'registration-user-creation','master','6126faa5-8c83-444b-acb3-3027c7de6f97',0,20,_binary '\0',NULL,NULL),('f75039b5-1598-47ee-9ddf-dc0c9a71cd15',NULL,'registration-user-creation','WESkit','f992dda7-3464-42c3-8c9d-0d755f02a984',0,20,_binary '\0',NULL,NULL),('faf8bb12-b882-43cc-ab83-81a76f1b5b05',NULL,NULL,'WESkit','8a00905d-0bac-4319-924b-b75ec71bc8b8',2,20,_binary '','a23902f0-020d-4487-b3b9-b7ac39d5d066',NULL),('fe60b298-2d0a-4fff-aeab-b16a13a7c5dc',NULL,'reset-credential-email','WESkit','51f3e5bf-c65b-4e46-8c25-6bd8f6a4c155',0,20,_binary '\0',NULL,NULL),('ffb319f8-83f3-427a-9ed5-8a8a8526c766',NULL,'registration-password-action','WESkit','f992dda7-3464-42c3-8c9d-0d755f02a984',0,50,_binary '\0',NULL,NULL);
/*!40000 ALTER TABLE `AUTHENTICATION_EXECUTION` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `AUTHENTICATION_FLOW`
--

DROP TABLE IF EXISTS `AUTHENTICATION_FLOW`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `AUTHENTICATION_FLOW` (
  `ID` varchar(36) NOT NULL,
  `ALIAS` varchar(255) DEFAULT NULL,
  `DESCRIPTION` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `REALM_ID` varchar(36) DEFAULT NULL,
  `PROVIDER_ID` varchar(36) NOT NULL DEFAULT 'basic-flow',
  `TOP_LEVEL` bit(1) NOT NULL DEFAULT b'0',
  `BUILT_IN` bit(1) NOT NULL DEFAULT b'0',
  PRIMARY KEY (`ID`),
  KEY `IDX_AUTH_FLOW_REALM` (`REALM_ID`),
  CONSTRAINT `FK_AUTH_FLOW_REALM` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AUTHENTICATION_FLOW`
--

LOCK TABLES `AUTHENTICATION_FLOW` WRITE;
/*!40000 ALTER TABLE `AUTHENTICATION_FLOW` DISABLE KEYS */;
INSERT INTO `AUTHENTICATION_FLOW` VALUES ('08d6c5ff-abc4-4d65-b9fc-e3372d62fcc0','direct grant','OpenID Connect Resource Owner Grant','master','basic-flow',_binary '',_binary ''),('1303b5e1-1f22-4599-b327-b25ef4392aff','Browser - Conditional OTP','Flow to determine if the OTP is required for the authentication','master','basic-flow',_binary '\0',_binary ''),('15841c4a-5579-46ad-9d29-db3c94df4ab7','Reset - Conditional OTP','Flow to determine if the OTP should be reset or not. Set to REQUIRED to force.','WESkit','basic-flow',_binary '\0',_binary ''),('178fbc31-cee8-4209-b189-79404bc1ece4','saml ecp','SAML ECP Profile Authentication Flow','master','basic-flow',_binary '',_binary ''),('2cf706ee-8d84-4ed2-ad89-8e78ac2a0a69','First broker login - Conditional OTP','Flow to determine if the OTP is required for the authentication','WESkit','basic-flow',_binary '\0',_binary ''),('30d3b23c-fb6d-41e0-afd8-f11714a972cb','docker auth','Used by Docker clients to authenticate against the IDP','WESkit','basic-flow',_binary '',_binary ''),('31a3c0f0-8aca-4afc-841a-da50e4f6b27d','Verify Existing Account by Re-authentication','Reauthentication of existing account','master','basic-flow',_binary '\0',_binary ''),('4ab909dd-030d-43a1-a69f-ce975803d511','docker auth','Used by Docker clients to authenticate against the IDP','master','basic-flow',_binary '',_binary ''),('51f3e5bf-c65b-4e46-8c25-6bd8f6a4c155','reset credentials','Reset credentials for a user if they forgot their password or something','WESkit','basic-flow',_binary '',_binary ''),('5f18bce2-ab51-4cc3-a574-8884c36c39db','Browser - Conditional OTP','Flow to determine if the OTP is required for the authentication','WESkit','basic-flow',_binary '\0',_binary ''),('6126faa5-8c83-444b-acb3-3027c7de6f97','registration form','registration form','master','form-flow',_binary '\0',_binary ''),('6ad3a3f0-62ca-45cc-a0e8-593e58c987c0','clients','Base authentication for clients','WESkit','client-flow',_binary '',_binary ''),('6d4b0963-75e8-4135-9e58-010a4ce602b7','Authentication Options','Authentication options.','WESkit','basic-flow',_binary '\0',_binary ''),('6e1a87bb-5fe8-45fc-b175-8876fd0fd500','Authentication Options','Authentication options.','master','basic-flow',_binary '\0',_binary ''),('746697f7-ec22-4046-948d-3a3518c6f26e','Handle Existing Account','Handle what to do if there is existing account with same email/username like authenticated identity provider','master','basic-flow',_binary '\0',_binary ''),('81d48717-e21f-425a-9232-7a11c63bd5b1','Direct Grant - Conditional OTP','Flow to determine if the OTP is required for the authentication','master','basic-flow',_binary '\0',_binary ''),('84399049-7a8f-41cd-93f2-ac5c275403fa','forms','Username, password, otp and other auth forms.','master','basic-flow',_binary '\0',_binary ''),('88aea7e1-06d3-48a2-bc87-2b0bee543f11','direct grant','OpenID Connect Resource Owner Grant','WESkit','basic-flow',_binary '',_binary ''),('8a00905d-0bac-4319-924b-b75ec71bc8b8','User creation or linking','Flow for the existing/non-existing user alternatives','WESkit','basic-flow',_binary '\0',_binary ''),('8e0430ce-ae65-4506-8fde-7ee28810407a','Reset - Conditional OTP','Flow to determine if the OTP should be reset or not. Set to REQUIRED to force.','master','basic-flow',_binary '\0',_binary ''),('92431b5a-91d0-4389-bb3e-2f5b3b4aee59','clients','Base authentication for clients','master','client-flow',_binary '',_binary ''),('92ed5a7a-96ae-4cb9-b56d-eb20a9dffcbb','browser','browser based authentication','WESkit','basic-flow',_binary '',_binary ''),('93343dd1-d31e-4814-a76b-0ef0f214fd2c','registration','registration flow','WESkit','basic-flow',_binary '',_binary ''),('9a9bfc27-6607-4f49-b011-6030c2f87f7f','http challenge','An authentication flow based on challenge-response HTTP Authentication Schemes','master','basic-flow',_binary '',_binary ''),('9d2106cf-7b6d-4462-96f0-d177e4a454b6','User creation or linking','Flow for the existing/non-existing user alternatives','master','basic-flow',_binary '\0',_binary ''),('a23902f0-020d-4487-b3b9-b7ac39d5d066','Handle Existing Account','Handle what to do if there is existing account with same email/username like authenticated identity provider','WESkit','basic-flow',_binary '\0',_binary ''),('b6f30b8f-0340-4d9b-9c69-7930569063da','first broker login','Actions taken after first broker login with identity provider account, which is not yet linked to any Keycloak account','master','basic-flow',_binary '',_binary ''),('bdd3adf6-08f7-466b-89b7-a8be23e23614','saml ecp','SAML ECP Profile Authentication Flow','WESkit','basic-flow',_binary '',_binary ''),('c0344e9e-b3cd-4468-9248-3fb84023a775','browser','browser based authentication','master','basic-flow',_binary '',_binary ''),('c1e93565-0e36-457b-b3e6-eff165c3e862','forms','Username, password, otp and other auth forms.','WESkit','basic-flow',_binary '\0',_binary ''),('c5ebe06f-1f65-41d9-bec0-9343c4eb9328','Direct Grant - Conditional OTP','Flow to determine if the OTP is required for the authentication','WESkit','basic-flow',_binary '\0',_binary ''),('d04b00e9-0d38-42cf-b01e-bb1186506485','reset credentials','Reset credentials for a user if they forgot their password or something','master','basic-flow',_binary '',_binary ''),('d4604f2f-8c94-4498-a548-621aed46af34','Account verification options','Method with which to verity the existing account','WESkit','basic-flow',_binary '\0',_binary ''),('d4f89522-a21d-4eca-9b27-e8ce91cc5694','first broker login','Actions taken after first broker login with identity provider account, which is not yet linked to any Keycloak account','WESkit','basic-flow',_binary '',_binary ''),('de5332d3-90ee-4b9c-91c9-6a59a5d3d49b','Account verification options','Method with which to verity the existing account','master','basic-flow',_binary '\0',_binary ''),('e3c65014-8f6d-4699-bd0f-5a60d857c1bf','First broker login - Conditional OTP','Flow to determine if the OTP is required for the authentication','master','basic-flow',_binary '\0',_binary ''),('ec4b4658-10f3-40f5-9b0c-54d76f7c5d9b','http challenge','An authentication flow based on challenge-response HTTP Authentication Schemes','WESkit','basic-flow',_binary '',_binary ''),('ef6ff606-c66a-4b1d-801c-e966c33c1b2a','registration','registration flow','master','basic-flow',_binary '',_binary ''),('f992dda7-3464-42c3-8c9d-0d755f02a984','registration form','registration form','WESkit','form-flow',_binary '\0',_binary ''),('fe42a8d7-5e5c-4014-9ec3-6d7de645d5e8','Verify Existing Account by Re-authentication','Reauthentication of existing account','WESkit','basic-flow',_binary '\0',_binary '');
/*!40000 ALTER TABLE `AUTHENTICATION_FLOW` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `AUTHENTICATOR_CONFIG`
--

DROP TABLE IF EXISTS `AUTHENTICATOR_CONFIG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `AUTHENTICATOR_CONFIG` (
  `ID` varchar(36) NOT NULL,
  `ALIAS` varchar(255) DEFAULT NULL,
  `REALM_ID` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_AUTH_CONFIG_REALM` (`REALM_ID`),
  CONSTRAINT `FK_AUTH_REALM` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AUTHENTICATOR_CONFIG`
--

LOCK TABLES `AUTHENTICATOR_CONFIG` WRITE;
/*!40000 ALTER TABLE `AUTHENTICATOR_CONFIG` DISABLE KEYS */;
INSERT INTO `AUTHENTICATOR_CONFIG` VALUES ('205ebd4b-8a3f-4584-a985-624c3e91e6e4','create unique user config','master'),('543f7589-961a-42cb-a419-5b4f9213b92b','create unique user config','WESkit'),('7ac056f1-c0b1-4f39-8076-eaedd1262a2a','review profile config','master'),('7b4273a8-b9a7-45f9-ab16-56c496143f28','review profile config','WESkit');
/*!40000 ALTER TABLE `AUTHENTICATOR_CONFIG` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `AUTHENTICATOR_CONFIG_ENTRY`
--

DROP TABLE IF EXISTS `AUTHENTICATOR_CONFIG_ENTRY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `AUTHENTICATOR_CONFIG_ENTRY` (
  `AUTHENTICATOR_ID` varchar(36) NOT NULL,
  `VALUE` longtext,
  `NAME` varchar(255) NOT NULL,
  PRIMARY KEY (`AUTHENTICATOR_ID`,`NAME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AUTHENTICATOR_CONFIG_ENTRY`
--

LOCK TABLES `AUTHENTICATOR_CONFIG_ENTRY` WRITE;
/*!40000 ALTER TABLE `AUTHENTICATOR_CONFIG_ENTRY` DISABLE KEYS */;
INSERT INTO `AUTHENTICATOR_CONFIG_ENTRY` VALUES ('205ebd4b-8a3f-4584-a985-624c3e91e6e4','false','require.password.update.after.registration'),('543f7589-961a-42cb-a419-5b4f9213b92b','false','require.password.update.after.registration'),('7ac056f1-c0b1-4f39-8076-eaedd1262a2a','missing','update.profile.on.first.login'),('7b4273a8-b9a7-45f9-ab16-56c496143f28','missing','update.profile.on.first.login');
/*!40000 ALTER TABLE `AUTHENTICATOR_CONFIG_ENTRY` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `BROKER_LINK`
--

DROP TABLE IF EXISTS `BROKER_LINK`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `BROKER_LINK` (
  `IDENTITY_PROVIDER` varchar(255) NOT NULL,
  `STORAGE_PROVIDER_ID` varchar(255) DEFAULT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  `BROKER_USER_ID` varchar(255) DEFAULT NULL,
  `BROKER_USERNAME` varchar(255) DEFAULT NULL,
  `TOKEN` text,
  `USER_ID` varchar(255) NOT NULL,
  PRIMARY KEY (`IDENTITY_PROVIDER`,`USER_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `BROKER_LINK`
--

LOCK TABLES `BROKER_LINK` WRITE;
/*!40000 ALTER TABLE `BROKER_LINK` DISABLE KEYS */;
/*!40000 ALTER TABLE `BROKER_LINK` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT`
--

DROP TABLE IF EXISTS `CLIENT`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT` (
  `ID` varchar(36) NOT NULL,
  `ENABLED` bit(1) NOT NULL DEFAULT b'0',
  `FULL_SCOPE_ALLOWED` bit(1) NOT NULL DEFAULT b'0',
  `CLIENT_ID` varchar(255) DEFAULT NULL,
  `NOT_BEFORE` int DEFAULT NULL,
  `PUBLIC_CLIENT` bit(1) NOT NULL DEFAULT b'0',
  `SECRET` varchar(255) DEFAULT NULL,
  `BASE_URL` varchar(255) DEFAULT NULL,
  `BEARER_ONLY` bit(1) NOT NULL DEFAULT b'0',
  `MANAGEMENT_URL` varchar(255) DEFAULT NULL,
  `SURROGATE_AUTH_REQUIRED` bit(1) NOT NULL DEFAULT b'0',
  `REALM_ID` varchar(36) DEFAULT NULL,
  `PROTOCOL` varchar(255) DEFAULT NULL,
  `NODE_REREG_TIMEOUT` int DEFAULT '0',
  `FRONTCHANNEL_LOGOUT` bit(1) NOT NULL DEFAULT b'0',
  `CONSENT_REQUIRED` bit(1) NOT NULL DEFAULT b'0',
  `NAME` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `SERVICE_ACCOUNTS_ENABLED` bit(1) NOT NULL DEFAULT b'0',
  `CLIENT_AUTHENTICATOR_TYPE` varchar(255) DEFAULT NULL,
  `ROOT_URL` varchar(255) DEFAULT NULL,
  `DESCRIPTION` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `REGISTRATION_TOKEN` varchar(255) DEFAULT NULL,
  `STANDARD_FLOW_ENABLED` bit(1) NOT NULL DEFAULT b'1',
  `IMPLICIT_FLOW_ENABLED` bit(1) NOT NULL DEFAULT b'0',
  `DIRECT_ACCESS_GRANTS_ENABLED` bit(1) NOT NULL DEFAULT b'0',
  `ALWAYS_DISPLAY_IN_CONSOLE` bit(1) NOT NULL DEFAULT b'0',
  PRIMARY KEY (`ID`),
  UNIQUE KEY `UK_B71CJLBENV945RB6GCON438AT` (`REALM_ID`,`CLIENT_ID`),
  KEY `IDX_CLIENT_ID` (`CLIENT_ID`),
  CONSTRAINT `FK_P56CTINXXB9GSK57FO49F9TAC` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT`
--

LOCK TABLES `CLIENT` WRITE;
/*!40000 ALTER TABLE `CLIENT` DISABLE KEYS */;
INSERT INTO `CLIENT` VALUES ('25671a13-17e4-4c92-abc6-58e5a2ed8630',_binary '',_binary '\0','admin-cli',0,_binary '','41da3b6c-6389-47c6-b19c-fd7dda005e95',NULL,_binary '\0',NULL,_binary '\0','master','openid-connect',0,_binary '\0',_binary '\0','${client_admin-cli}',_binary '\0','client-secret',NULL,NULL,NULL,_binary '\0',_binary '\0',_binary '',_binary '\0'),('25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '',_binary '\0','realm-management',0,_binary '\0','**********',NULL,_binary '',NULL,_binary '\0','WESkit','openid-connect',0,_binary '\0',_binary '\0','${client_realm-management}',_binary '\0','client-secret',NULL,NULL,NULL,_binary '',_binary '\0',_binary '\0',_binary '\0'),('2ba5388c-d47c-4d80-b9bd-3d9bab15f3be',_binary '',_binary '\0','broker',0,_binary '\0','**********',NULL,_binary '\0',NULL,_binary '\0','WESkit','openid-connect',0,_binary '\0',_binary '\0','${client_broker}',_binary '\0','client-secret',NULL,NULL,NULL,_binary '',_binary '\0',_binary '\0',_binary '\0'),('3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '',_binary '','master-realm',0,_binary '\0','8ae09321-89d7-4e7a-8473-e0fbb03d6e5f',NULL,_binary '',NULL,_binary '\0','master',NULL,0,_binary '\0',_binary '\0','master Realm',_binary '\0','client-secret',NULL,NULL,NULL,_binary '',_binary '\0',_binary '\0',_binary '\0'),('48ca4365-c4d8-477b-91ce-d3509dc77334',_binary '',_binary '','WESkit',0,_binary '\0','a8086bcc-44f3-40f9-9e15-fd5c3c98ab24','https://localhost:5000/',_binary '\0','',_binary '\0','WESkit','openid-connect',-1,_binary '\0',_binary '\0','WESkit',_binary '\0','client-secret','','WESkit',NULL,_binary '',_binary '\0',_binary '',_binary '\0'),('4b528bc5-f5d0-446f-834d-5b834ea41103',_binary '',_binary '','WESkitWEBClient',0,_binary '\0','5be0c5e9-5e49-468c-9bf7-9ba0944c5604',NULL,_binary '\0',NULL,_binary '\0','WESkit','openid-connect',-1,_binary '\0',_binary '\0',NULL,_binary '\0','client-secret',NULL,NULL,NULL,_binary '',_binary '\0',_binary '',_binary '\0'),('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a',_binary '',_binary '\0','security-admin-console',0,_binary '','7cf41e7e-d09b-4c84-ac4b-799e87be22ad','/admin/master/console/',_binary '\0',NULL,_binary '\0','master','openid-connect',0,_binary '\0',_binary '\0','${client_security-admin-console}',_binary '\0','client-secret','${authAdminUrl}',NULL,NULL,_binary '',_binary '\0',_binary '\0',_binary '\0'),('5060e61b-233b-4347-94e2-4d84d3e67dcc',_binary '',_binary '\0','account-console',0,_binary '','661a10d9-9ee9-4227-b5ec-bb757cbf1868','/realms/master/account/',_binary '\0',NULL,_binary '\0','master','openid-connect',0,_binary '\0',_binary '\0','${client_account-console}',_binary '\0','client-secret','${authBaseUrl}',NULL,NULL,_binary '',_binary '\0',_binary '\0',_binary '\0'),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae',_binary '',_binary '\0','security-admin-console',0,_binary '','**********','/admin/WESkit/console/',_binary '\0',NULL,_binary '\0','WESkit','openid-connect',0,_binary '\0',_binary '\0','${client_security-admin-console}',_binary '\0','client-secret','${authAdminUrl}',NULL,NULL,_binary '',_binary '\0',_binary '\0',_binary '\0'),('69131d51-8b86-4470-a07c-a51305df8782',_binary '',_binary '','WESkit-realm',0,_binary '\0','e66c4876-3d09-4ef8-a27c-8132409b8b8d',NULL,_binary '',NULL,_binary '\0','master',NULL,0,_binary '\0',_binary '\0','WESkit Realm',_binary '\0','client-secret',NULL,NULL,NULL,_binary '',_binary '\0',_binary '\0',_binary '\0'),('77249ec3-5596-4d8b-a2d3-15604ca70de5',_binary '',_binary '\0','account',0,_binary '\0','**********','/realms/WESkit/account/',_binary '\0',NULL,_binary '\0','WESkit','openid-connect',0,_binary '\0',_binary '\0','${client_account}',_binary '\0','client-secret','${authBaseUrl}',NULL,NULL,_binary '',_binary '\0',_binary '\0',_binary '\0'),('8ae1bc8c-be2e-4b41-943c-63bd2aaf0e03',_binary '',_binary '\0','broker',0,_binary '\0','e8f2725e-a434-4a9f-9916-36b7dda7e468',NULL,_binary '\0',NULL,_binary '\0','master','openid-connect',0,_binary '\0',_binary '\0','${client_broker}',_binary '\0','client-secret',NULL,NULL,NULL,_binary '',_binary '\0',_binary '\0',_binary '\0'),('bf810e04-c833-40e0-9170-b2a6ca33ce32',_binary '',_binary '\0','admin-cli',0,_binary '','**********',NULL,_binary '\0',NULL,_binary '\0','WESkit','openid-connect',0,_binary '\0',_binary '\0','${client_admin-cli}',_binary '\0','client-secret',NULL,NULL,NULL,_binary '\0',_binary '\0',_binary '',_binary '\0'),('e43e0012-146a-42a3-909a-59ac2a345d24',_binary '',_binary '','OTP',0,_binary '\0','7670fd00-9318-44c2-bda3-1a1d2743492d',NULL,_binary '\0',NULL,_binary '\0','WESkit','openid-connect',-1,_binary '\0',_binary '\0',NULL,_binary '\0','client-secret',NULL,NULL,NULL,_binary '\0',_binary '\0',_binary '',_binary '\0'),('e47088a1-3190-435b-a237-e4e0b50988d5',_binary '',_binary '\0','account',0,_binary '\0','33c3e838-eb8b-41ef-9713-40b5ce72a6be','/realms/master/account/',_binary '\0',NULL,_binary '\0','master','openid-connect',0,_binary '\0',_binary '\0','${client_account}',_binary '\0','client-secret','${authBaseUrl}',NULL,NULL,_binary '',_binary '\0',_binary '\0',_binary '\0'),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03',_binary '',_binary '\0','account-console',0,_binary '','**********','/realms/WESkit/account/',_binary '\0',NULL,_binary '\0','WESkit','openid-connect',0,_binary '\0',_binary '\0','${client_account-console}',_binary '\0','client-secret','${authBaseUrl}',NULL,NULL,_binary '',_binary '\0',_binary '\0',_binary '\0');
/*!40000 ALTER TABLE `CLIENT` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_ATTRIBUTES`
--

DROP TABLE IF EXISTS `CLIENT_ATTRIBUTES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_ATTRIBUTES` (
  `CLIENT_ID` varchar(36) NOT NULL,
  `VALUE` text,
  `NAME` varchar(255) NOT NULL,
  PRIMARY KEY (`CLIENT_ID`,`NAME`),
  CONSTRAINT `FK3C47C64BEACCA966` FOREIGN KEY (`CLIENT_ID`) REFERENCES `CLIENT` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_ATTRIBUTES`
--

LOCK TABLES `CLIENT_ATTRIBUTES` WRITE;
/*!40000 ALTER TABLE `CLIENT_ATTRIBUTES` DISABLE KEYS */;
INSERT INTO `CLIENT_ATTRIBUTES` VALUES ('48ca4365-c4d8-477b-91ce-d3509dc77334','false','backchannel.logout.revoke.offline.tokens'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','backchannel.logout.session.required'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','client_credentials.use_refresh_token'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','display.on.consent.screen'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','exclude.session.state.from.auth.response'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','saml_force_name_id_format'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','saml.assertion.signature'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','saml.authnstatement'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','saml.client.signature'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','saml.encrypt'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','saml.force.post.binding'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','saml.multivalued.roles'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','saml.onetimeuse.condition'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','saml.server.signature'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','saml.server.signature.keyinfo.ext'),('48ca4365-c4d8-477b-91ce-d3509dc77334','false','tls.client.certificate.bound.access.tokens'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','backchannel.logout.revoke.offline.tokens'),('4b528bc5-f5d0-446f-834d-5b834ea41103','true','backchannel.logout.session.required'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','client_credentials.use_refresh_token'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','display.on.consent.screen'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','exclude.session.state.from.auth.response'),('4b528bc5-f5d0-446f-834d-5b834ea41103',NULL,'request.uris'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','saml_force_name_id_format'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','saml.assertion.signature'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','saml.authnstatement'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','saml.client.signature'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','saml.encrypt'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','saml.force.post.binding'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','saml.multivalued.roles'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','saml.onetimeuse.condition'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','saml.server.signature'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','saml.server.signature.keyinfo.ext'),('4b528bc5-f5d0-446f-834d-5b834ea41103','false','tls.client.certificate.bound.access.tokens'),('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a','S256','pkce.code.challenge.method'),('5060e61b-233b-4347-94e2-4d84d3e67dcc','S256','pkce.code.challenge.method'),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae','S256','pkce.code.challenge.method'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','backchannel.logout.revoke.offline.tokens'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','backchannel.logout.session.required'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','client_credentials.use_refresh_token'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','display.on.consent.screen'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','exclude.session.state.from.auth.response'),('e43e0012-146a-42a3-909a-59ac2a345d24',NULL,'request.uris'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','saml_force_name_id_format'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','saml.assertion.signature'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','saml.authnstatement'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','saml.client.signature'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','saml.encrypt'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','saml.force.post.binding'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','saml.multivalued.roles'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','saml.onetimeuse.condition'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','saml.server.signature'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','saml.server.signature.keyinfo.ext'),('e43e0012-146a-42a3-909a-59ac2a345d24','false','tls.client.certificate.bound.access.tokens'),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03','S256','pkce.code.challenge.method');
/*!40000 ALTER TABLE `CLIENT_ATTRIBUTES` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_AUTH_FLOW_BINDINGS`
--

DROP TABLE IF EXISTS `CLIENT_AUTH_FLOW_BINDINGS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_AUTH_FLOW_BINDINGS` (
  `CLIENT_ID` varchar(36) NOT NULL,
  `FLOW_ID` varchar(36) DEFAULT NULL,
  `BINDING_NAME` varchar(255) NOT NULL,
  PRIMARY KEY (`CLIENT_ID`,`BINDING_NAME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_AUTH_FLOW_BINDINGS`
--

LOCK TABLES `CLIENT_AUTH_FLOW_BINDINGS` WRITE;
/*!40000 ALTER TABLE `CLIENT_AUTH_FLOW_BINDINGS` DISABLE KEYS */;
/*!40000 ALTER TABLE `CLIENT_AUTH_FLOW_BINDINGS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_DEFAULT_ROLES`
--

DROP TABLE IF EXISTS `CLIENT_DEFAULT_ROLES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_DEFAULT_ROLES` (
  `CLIENT_ID` varchar(36) NOT NULL,
  `ROLE_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`CLIENT_ID`,`ROLE_ID`),
  UNIQUE KEY `UK_8AELWNIBJI49AVXSRTUF6XJOW` (`ROLE_ID`),
  KEY `IDX_CLIENT_DEF_ROLES_CLIENT` (`CLIENT_ID`),
  CONSTRAINT `FK_NUILTS7KLWQW2H8M2B5JOYTKY` FOREIGN KEY (`CLIENT_ID`) REFERENCES `CLIENT` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_DEFAULT_ROLES`
--

LOCK TABLES `CLIENT_DEFAULT_ROLES` WRITE;
/*!40000 ALTER TABLE `CLIENT_DEFAULT_ROLES` DISABLE KEYS */;
INSERT INTO `CLIENT_DEFAULT_ROLES` VALUES ('e47088a1-3190-435b-a237-e4e0b50988d5','248a3f39-6dfe-422f-8c29-70c6669842fc'),('77249ec3-5596-4d8b-a2d3-15604ca70de5','9fe0f5ad-7ef3-4cd5-b216-9fc0e4021bf4'),('e47088a1-3190-435b-a237-e4e0b50988d5','b0025059-e023-4fde-836c-a0e12b9941b6'),('77249ec3-5596-4d8b-a2d3-15604ca70de5','e963003d-a6f9-40e1-a14d-df4af02da9be');
/*!40000 ALTER TABLE `CLIENT_DEFAULT_ROLES` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_INITIAL_ACCESS`
--

DROP TABLE IF EXISTS `CLIENT_INITIAL_ACCESS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_INITIAL_ACCESS` (
  `ID` varchar(36) NOT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  `TIMESTAMP` int DEFAULT NULL,
  `EXPIRATION` int DEFAULT NULL,
  `COUNT` int DEFAULT NULL,
  `REMAINING_COUNT` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_CLIENT_INIT_ACC_REALM` (`REALM_ID`),
  CONSTRAINT `FK_CLIENT_INIT_ACC_REALM` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_INITIAL_ACCESS`
--

LOCK TABLES `CLIENT_INITIAL_ACCESS` WRITE;
/*!40000 ALTER TABLE `CLIENT_INITIAL_ACCESS` DISABLE KEYS */;
/*!40000 ALTER TABLE `CLIENT_INITIAL_ACCESS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_NODE_REGISTRATIONS`
--

DROP TABLE IF EXISTS `CLIENT_NODE_REGISTRATIONS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_NODE_REGISTRATIONS` (
  `CLIENT_ID` varchar(36) NOT NULL,
  `VALUE` int DEFAULT NULL,
  `NAME` varchar(255) NOT NULL,
  PRIMARY KEY (`CLIENT_ID`,`NAME`),
  CONSTRAINT `FK4129723BA992F594` FOREIGN KEY (`CLIENT_ID`) REFERENCES `CLIENT` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_NODE_REGISTRATIONS`
--

LOCK TABLES `CLIENT_NODE_REGISTRATIONS` WRITE;
/*!40000 ALTER TABLE `CLIENT_NODE_REGISTRATIONS` DISABLE KEYS */;
/*!40000 ALTER TABLE `CLIENT_NODE_REGISTRATIONS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_SCOPE`
--

DROP TABLE IF EXISTS `CLIENT_SCOPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_SCOPE` (
  `ID` varchar(36) NOT NULL,
  `NAME` varchar(255) DEFAULT NULL,
  `REALM_ID` varchar(36) DEFAULT NULL,
  `DESCRIPTION` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `PROTOCOL` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `UK_CLI_SCOPE` (`REALM_ID`,`NAME`),
  KEY `IDX_REALM_CLSCOPE` (`REALM_ID`),
  CONSTRAINT `FK_REALM_CLI_SCOPE` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_SCOPE`
--

LOCK TABLES `CLIENT_SCOPE` WRITE;
/*!40000 ALTER TABLE `CLIENT_SCOPE` DISABLE KEYS */;
INSERT INTO `CLIENT_SCOPE` VALUES ('1d548a75-32d2-458d-96e5-772421f7c1bd','email','WESkit','OpenID Connect built-in scope: email','openid-connect'),('1f6b4061-797c-4caf-b130-c7ced3da55a7','roles','WESkit','OpenID Connect scope for add user roles to the access token','openid-connect'),('1fdf2898-fa16-457d-8d1b-89e86e0bef77','role_list','master','SAML role list','saml'),('21ac849d-f14e-4ecf-9e98-dc065603e167','profile','WESkit','OpenID Connect built-in scope: profile','openid-connect'),('4b170f2c-e31b-4d03-8a2a-b514b444bfa6','phone','master','OpenID Connect built-in scope: phone','openid-connect'),('5bbfcb16-0bcb-49e6-a25c-a2ac6c795864','roles','master','OpenID Connect scope for add user roles to the access token','openid-connect'),('61cab59a-456f-4bc2-b11c-4398c498dd12','profile','master','OpenID Connect built-in scope: profile','openid-connect'),('69e1f2f9-5014-47df-b6aa-91ca814888df','web-origins','master','OpenID Connect scope for add allowed web origins to the access token','openid-connect'),('9730d937-6ad4-4e39-a78c-176e16c88b8f','microprofile-jwt','master','Microprofile - JWT built-in scope','openid-connect'),('a968f0db-2113-4e70-960f-3c2e1c1d3e94','phone','WESkit','OpenID Connect built-in scope: phone','openid-connect'),('bd2d9561-e102-45f0-a7c5-8fa07a8f925b','web-origins','WESkit','OpenID Connect scope for add allowed web origins to the access token','openid-connect'),('bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb','role_list','WESkit','SAML role list','saml'),('c6151be7-666a-487a-ad06-615fe9997983','offline_access','WESkit','OpenID Connect built-in scope: offline_access','openid-connect'),('d2557dc6-b207-4785-9db3-e88e0eca290c','address','master','OpenID Connect built-in scope: address','openid-connect'),('d4b72e00-8775-47e0-8412-8cac6a2c3054','address','WESkit','OpenID Connect built-in scope: address','openid-connect'),('d7825fa7-20e1-43af-9ced-2a9d44117616','microprofile-jwt','WESkit','Microprofile - JWT built-in scope','openid-connect'),('d8f588a9-7bb7-41be-ba22-d9b75e9a8195','offline_access','master','OpenID Connect built-in scope: offline_access','openid-connect'),('daf2f7b7-f1c7-458f-8a62-d72cc891a82d','email','master','OpenID Connect built-in scope: email','openid-connect');
/*!40000 ALTER TABLE `CLIENT_SCOPE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_SCOPE_ATTRIBUTES`
--

DROP TABLE IF EXISTS `CLIENT_SCOPE_ATTRIBUTES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_SCOPE_ATTRIBUTES` (
  `SCOPE_ID` varchar(36) NOT NULL,
  `VALUE` text,
  `NAME` varchar(255) NOT NULL,
  PRIMARY KEY (`SCOPE_ID`,`NAME`),
  KEY `IDX_CLSCOPE_ATTRS` (`SCOPE_ID`),
  CONSTRAINT `FK_CL_SCOPE_ATTR_SCOPE` FOREIGN KEY (`SCOPE_ID`) REFERENCES `CLIENT_SCOPE` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_SCOPE_ATTRIBUTES`
--

LOCK TABLES `CLIENT_SCOPE_ATTRIBUTES` WRITE;
/*!40000 ALTER TABLE `CLIENT_SCOPE_ATTRIBUTES` DISABLE KEYS */;
INSERT INTO `CLIENT_SCOPE_ATTRIBUTES` VALUES ('1d548a75-32d2-458d-96e5-772421f7c1bd','${emailScopeConsentText}','consent.screen.text'),('1d548a75-32d2-458d-96e5-772421f7c1bd','true','display.on.consent.screen'),('1d548a75-32d2-458d-96e5-772421f7c1bd','true','include.in.token.scope'),('1f6b4061-797c-4caf-b130-c7ced3da55a7','${rolesScopeConsentText}','consent.screen.text'),('1f6b4061-797c-4caf-b130-c7ced3da55a7','true','display.on.consent.screen'),('1f6b4061-797c-4caf-b130-c7ced3da55a7','false','include.in.token.scope'),('1fdf2898-fa16-457d-8d1b-89e86e0bef77','${samlRoleListScopeConsentText}','consent.screen.text'),('1fdf2898-fa16-457d-8d1b-89e86e0bef77','true','display.on.consent.screen'),('21ac849d-f14e-4ecf-9e98-dc065603e167','${profileScopeConsentText}','consent.screen.text'),('21ac849d-f14e-4ecf-9e98-dc065603e167','true','display.on.consent.screen'),('21ac849d-f14e-4ecf-9e98-dc065603e167','true','include.in.token.scope'),('4b170f2c-e31b-4d03-8a2a-b514b444bfa6','${phoneScopeConsentText}','consent.screen.text'),('4b170f2c-e31b-4d03-8a2a-b514b444bfa6','true','display.on.consent.screen'),('4b170f2c-e31b-4d03-8a2a-b514b444bfa6','true','include.in.token.scope'),('5bbfcb16-0bcb-49e6-a25c-a2ac6c795864','${rolesScopeConsentText}','consent.screen.text'),('5bbfcb16-0bcb-49e6-a25c-a2ac6c795864','true','display.on.consent.screen'),('5bbfcb16-0bcb-49e6-a25c-a2ac6c795864','false','include.in.token.scope'),('61cab59a-456f-4bc2-b11c-4398c498dd12','${profileScopeConsentText}','consent.screen.text'),('61cab59a-456f-4bc2-b11c-4398c498dd12','true','display.on.consent.screen'),('61cab59a-456f-4bc2-b11c-4398c498dd12','true','include.in.token.scope'),('69e1f2f9-5014-47df-b6aa-91ca814888df','','consent.screen.text'),('69e1f2f9-5014-47df-b6aa-91ca814888df','false','display.on.consent.screen'),('69e1f2f9-5014-47df-b6aa-91ca814888df','false','include.in.token.scope'),('9730d937-6ad4-4e39-a78c-176e16c88b8f','false','display.on.consent.screen'),('9730d937-6ad4-4e39-a78c-176e16c88b8f','true','include.in.token.scope'),('a968f0db-2113-4e70-960f-3c2e1c1d3e94','${phoneScopeConsentText}','consent.screen.text'),('a968f0db-2113-4e70-960f-3c2e1c1d3e94','true','display.on.consent.screen'),('a968f0db-2113-4e70-960f-3c2e1c1d3e94','true','include.in.token.scope'),('bd2d9561-e102-45f0-a7c5-8fa07a8f925b','','consent.screen.text'),('bd2d9561-e102-45f0-a7c5-8fa07a8f925b','false','display.on.consent.screen'),('bd2d9561-e102-45f0-a7c5-8fa07a8f925b','false','include.in.token.scope'),('bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb','${samlRoleListScopeConsentText}','consent.screen.text'),('bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb','true','display.on.consent.screen'),('c6151be7-666a-487a-ad06-615fe9997983','${offlineAccessScopeConsentText}','consent.screen.text'),('c6151be7-666a-487a-ad06-615fe9997983','true','display.on.consent.screen'),('d2557dc6-b207-4785-9db3-e88e0eca290c','${addressScopeConsentText}','consent.screen.text'),('d2557dc6-b207-4785-9db3-e88e0eca290c','true','display.on.consent.screen'),('d2557dc6-b207-4785-9db3-e88e0eca290c','true','include.in.token.scope'),('d4b72e00-8775-47e0-8412-8cac6a2c3054','${addressScopeConsentText}','consent.screen.text'),('d4b72e00-8775-47e0-8412-8cac6a2c3054','true','display.on.consent.screen'),('d4b72e00-8775-47e0-8412-8cac6a2c3054','true','include.in.token.scope'),('d7825fa7-20e1-43af-9ced-2a9d44117616','false','display.on.consent.screen'),('d7825fa7-20e1-43af-9ced-2a9d44117616','true','include.in.token.scope'),('d8f588a9-7bb7-41be-ba22-d9b75e9a8195','${offlineAccessScopeConsentText}','consent.screen.text'),('d8f588a9-7bb7-41be-ba22-d9b75e9a8195','true','display.on.consent.screen'),('daf2f7b7-f1c7-458f-8a62-d72cc891a82d','${emailScopeConsentText}','consent.screen.text'),('daf2f7b7-f1c7-458f-8a62-d72cc891a82d','true','display.on.consent.screen'),('daf2f7b7-f1c7-458f-8a62-d72cc891a82d','true','include.in.token.scope');
/*!40000 ALTER TABLE `CLIENT_SCOPE_ATTRIBUTES` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_SCOPE_CLIENT`
--

DROP TABLE IF EXISTS `CLIENT_SCOPE_CLIENT`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_SCOPE_CLIENT` (
  `CLIENT_ID` varchar(36) NOT NULL,
  `SCOPE_ID` varchar(36) NOT NULL,
  `DEFAULT_SCOPE` bit(1) NOT NULL DEFAULT b'0',
  PRIMARY KEY (`CLIENT_ID`,`SCOPE_ID`),
  KEY `IDX_CLSCOPE_CL` (`CLIENT_ID`),
  KEY `IDX_CL_CLSCOPE` (`SCOPE_ID`),
  CONSTRAINT `FK_C_CLI_SCOPE_CLIENT` FOREIGN KEY (`CLIENT_ID`) REFERENCES `CLIENT` (`ID`),
  CONSTRAINT `FK_C_CLI_SCOPE_SCOPE` FOREIGN KEY (`SCOPE_ID`) REFERENCES `CLIENT_SCOPE` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_SCOPE_CLIENT`
--

LOCK TABLES `CLIENT_SCOPE_CLIENT` WRITE;
/*!40000 ALTER TABLE `CLIENT_SCOPE_CLIENT` DISABLE KEYS */;
INSERT INTO `CLIENT_SCOPE_CLIENT` VALUES ('25671a13-17e4-4c92-abc6-58e5a2ed8630','1fdf2898-fa16-457d-8d1b-89e86e0bef77',_binary ''),('25671a13-17e4-4c92-abc6-58e5a2ed8630','4b170f2c-e31b-4d03-8a2a-b514b444bfa6',_binary '\0'),('25671a13-17e4-4c92-abc6-58e5a2ed8630','5bbfcb16-0bcb-49e6-a25c-a2ac6c795864',_binary ''),('25671a13-17e4-4c92-abc6-58e5a2ed8630','61cab59a-456f-4bc2-b11c-4398c498dd12',_binary ''),('25671a13-17e4-4c92-abc6-58e5a2ed8630','69e1f2f9-5014-47df-b6aa-91ca814888df',_binary ''),('25671a13-17e4-4c92-abc6-58e5a2ed8630','9730d937-6ad4-4e39-a78c-176e16c88b8f',_binary '\0'),('25671a13-17e4-4c92-abc6-58e5a2ed8630','d2557dc6-b207-4785-9db3-e88e0eca290c',_binary '\0'),('25671a13-17e4-4c92-abc6-58e5a2ed8630','d8f588a9-7bb7-41be-ba22-d9b75e9a8195',_binary '\0'),('25671a13-17e4-4c92-abc6-58e5a2ed8630','daf2f7b7-f1c7-458f-8a62-d72cc891a82d',_binary ''),('25c61f98-bb03-41f6-b5d1-53e0884aa1c4','1d548a75-32d2-458d-96e5-772421f7c1bd',_binary ''),('25c61f98-bb03-41f6-b5d1-53e0884aa1c4','1f6b4061-797c-4caf-b130-c7ced3da55a7',_binary ''),('25c61f98-bb03-41f6-b5d1-53e0884aa1c4','21ac849d-f14e-4ecf-9e98-dc065603e167',_binary ''),('25c61f98-bb03-41f6-b5d1-53e0884aa1c4','a968f0db-2113-4e70-960f-3c2e1c1d3e94',_binary '\0'),('25c61f98-bb03-41f6-b5d1-53e0884aa1c4','bd2d9561-e102-45f0-a7c5-8fa07a8f925b',_binary ''),('25c61f98-bb03-41f6-b5d1-53e0884aa1c4','bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb',_binary ''),('25c61f98-bb03-41f6-b5d1-53e0884aa1c4','c6151be7-666a-487a-ad06-615fe9997983',_binary '\0'),('25c61f98-bb03-41f6-b5d1-53e0884aa1c4','d4b72e00-8775-47e0-8412-8cac6a2c3054',_binary '\0'),('25c61f98-bb03-41f6-b5d1-53e0884aa1c4','d7825fa7-20e1-43af-9ced-2a9d44117616',_binary '\0'),('2ba5388c-d47c-4d80-b9bd-3d9bab15f3be','1d548a75-32d2-458d-96e5-772421f7c1bd',_binary ''),('2ba5388c-d47c-4d80-b9bd-3d9bab15f3be','1f6b4061-797c-4caf-b130-c7ced3da55a7',_binary ''),('2ba5388c-d47c-4d80-b9bd-3d9bab15f3be','21ac849d-f14e-4ecf-9e98-dc065603e167',_binary ''),('2ba5388c-d47c-4d80-b9bd-3d9bab15f3be','a968f0db-2113-4e70-960f-3c2e1c1d3e94',_binary '\0'),('2ba5388c-d47c-4d80-b9bd-3d9bab15f3be','bd2d9561-e102-45f0-a7c5-8fa07a8f925b',_binary ''),('2ba5388c-d47c-4d80-b9bd-3d9bab15f3be','bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb',_binary ''),('2ba5388c-d47c-4d80-b9bd-3d9bab15f3be','c6151be7-666a-487a-ad06-615fe9997983',_binary '\0'),('2ba5388c-d47c-4d80-b9bd-3d9bab15f3be','d4b72e00-8775-47e0-8412-8cac6a2c3054',_binary '\0'),('2ba5388c-d47c-4d80-b9bd-3d9bab15f3be','d7825fa7-20e1-43af-9ced-2a9d44117616',_binary '\0'),('3e40f193-9407-4729-88c2-95fcc3ab220f','1fdf2898-fa16-457d-8d1b-89e86e0bef77',_binary ''),('3e40f193-9407-4729-88c2-95fcc3ab220f','4b170f2c-e31b-4d03-8a2a-b514b444bfa6',_binary '\0'),('3e40f193-9407-4729-88c2-95fcc3ab220f','5bbfcb16-0bcb-49e6-a25c-a2ac6c795864',_binary ''),('3e40f193-9407-4729-88c2-95fcc3ab220f','61cab59a-456f-4bc2-b11c-4398c498dd12',_binary ''),('3e40f193-9407-4729-88c2-95fcc3ab220f','69e1f2f9-5014-47df-b6aa-91ca814888df',_binary ''),('3e40f193-9407-4729-88c2-95fcc3ab220f','9730d937-6ad4-4e39-a78c-176e16c88b8f',_binary '\0'),('3e40f193-9407-4729-88c2-95fcc3ab220f','d2557dc6-b207-4785-9db3-e88e0eca290c',_binary '\0'),('3e40f193-9407-4729-88c2-95fcc3ab220f','d8f588a9-7bb7-41be-ba22-d9b75e9a8195',_binary '\0'),('3e40f193-9407-4729-88c2-95fcc3ab220f','daf2f7b7-f1c7-458f-8a62-d72cc891a82d',_binary ''),('48ca4365-c4d8-477b-91ce-d3509dc77334','1d548a75-32d2-458d-96e5-772421f7c1bd',_binary ''),('48ca4365-c4d8-477b-91ce-d3509dc77334','1f6b4061-797c-4caf-b130-c7ced3da55a7',_binary ''),('48ca4365-c4d8-477b-91ce-d3509dc77334','21ac849d-f14e-4ecf-9e98-dc065603e167',_binary ''),('48ca4365-c4d8-477b-91ce-d3509dc77334','a968f0db-2113-4e70-960f-3c2e1c1d3e94',_binary '\0'),('48ca4365-c4d8-477b-91ce-d3509dc77334','bd2d9561-e102-45f0-a7c5-8fa07a8f925b',_binary ''),('48ca4365-c4d8-477b-91ce-d3509dc77334','bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb',_binary ''),('48ca4365-c4d8-477b-91ce-d3509dc77334','c6151be7-666a-487a-ad06-615fe9997983',_binary '\0'),('48ca4365-c4d8-477b-91ce-d3509dc77334','d4b72e00-8775-47e0-8412-8cac6a2c3054',_binary '\0'),('48ca4365-c4d8-477b-91ce-d3509dc77334','d7825fa7-20e1-43af-9ced-2a9d44117616',_binary '\0'),('4b528bc5-f5d0-446f-834d-5b834ea41103','1d548a75-32d2-458d-96e5-772421f7c1bd',_binary ''),('4b528bc5-f5d0-446f-834d-5b834ea41103','1f6b4061-797c-4caf-b130-c7ced3da55a7',_binary ''),('4b528bc5-f5d0-446f-834d-5b834ea41103','21ac849d-f14e-4ecf-9e98-dc065603e167',_binary ''),('4b528bc5-f5d0-446f-834d-5b834ea41103','a968f0db-2113-4e70-960f-3c2e1c1d3e94',_binary '\0'),('4b528bc5-f5d0-446f-834d-5b834ea41103','bd2d9561-e102-45f0-a7c5-8fa07a8f925b',_binary ''),('4b528bc5-f5d0-446f-834d-5b834ea41103','bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb',_binary ''),('4b528bc5-f5d0-446f-834d-5b834ea41103','c6151be7-666a-487a-ad06-615fe9997983',_binary '\0'),('4b528bc5-f5d0-446f-834d-5b834ea41103','d4b72e00-8775-47e0-8412-8cac6a2c3054',_binary '\0'),('4b528bc5-f5d0-446f-834d-5b834ea41103','d7825fa7-20e1-43af-9ced-2a9d44117616',_binary '\0'),('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a','1fdf2898-fa16-457d-8d1b-89e86e0bef77',_binary ''),('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a','4b170f2c-e31b-4d03-8a2a-b514b444bfa6',_binary '\0'),('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a','5bbfcb16-0bcb-49e6-a25c-a2ac6c795864',_binary ''),('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a','61cab59a-456f-4bc2-b11c-4398c498dd12',_binary ''),('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a','69e1f2f9-5014-47df-b6aa-91ca814888df',_binary ''),('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a','9730d937-6ad4-4e39-a78c-176e16c88b8f',_binary '\0'),('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a','d2557dc6-b207-4785-9db3-e88e0eca290c',_binary '\0'),('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a','d8f588a9-7bb7-41be-ba22-d9b75e9a8195',_binary '\0'),('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a','daf2f7b7-f1c7-458f-8a62-d72cc891a82d',_binary ''),('5060e61b-233b-4347-94e2-4d84d3e67dcc','1fdf2898-fa16-457d-8d1b-89e86e0bef77',_binary ''),('5060e61b-233b-4347-94e2-4d84d3e67dcc','4b170f2c-e31b-4d03-8a2a-b514b444bfa6',_binary '\0'),('5060e61b-233b-4347-94e2-4d84d3e67dcc','5bbfcb16-0bcb-49e6-a25c-a2ac6c795864',_binary ''),('5060e61b-233b-4347-94e2-4d84d3e67dcc','61cab59a-456f-4bc2-b11c-4398c498dd12',_binary ''),('5060e61b-233b-4347-94e2-4d84d3e67dcc','69e1f2f9-5014-47df-b6aa-91ca814888df',_binary ''),('5060e61b-233b-4347-94e2-4d84d3e67dcc','9730d937-6ad4-4e39-a78c-176e16c88b8f',_binary '\0'),('5060e61b-233b-4347-94e2-4d84d3e67dcc','d2557dc6-b207-4785-9db3-e88e0eca290c',_binary '\0'),('5060e61b-233b-4347-94e2-4d84d3e67dcc','d8f588a9-7bb7-41be-ba22-d9b75e9a8195',_binary '\0'),('5060e61b-233b-4347-94e2-4d84d3e67dcc','daf2f7b7-f1c7-458f-8a62-d72cc891a82d',_binary ''),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae','1d548a75-32d2-458d-96e5-772421f7c1bd',_binary ''),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae','1f6b4061-797c-4caf-b130-c7ced3da55a7',_binary ''),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae','21ac849d-f14e-4ecf-9e98-dc065603e167',_binary ''),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae','a968f0db-2113-4e70-960f-3c2e1c1d3e94',_binary '\0'),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae','bd2d9561-e102-45f0-a7c5-8fa07a8f925b',_binary ''),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae','bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb',_binary ''),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae','c6151be7-666a-487a-ad06-615fe9997983',_binary '\0'),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae','d4b72e00-8775-47e0-8412-8cac6a2c3054',_binary '\0'),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae','d7825fa7-20e1-43af-9ced-2a9d44117616',_binary '\0'),('69131d51-8b86-4470-a07c-a51305df8782','1fdf2898-fa16-457d-8d1b-89e86e0bef77',_binary ''),('69131d51-8b86-4470-a07c-a51305df8782','4b170f2c-e31b-4d03-8a2a-b514b444bfa6',_binary '\0'),('69131d51-8b86-4470-a07c-a51305df8782','5bbfcb16-0bcb-49e6-a25c-a2ac6c795864',_binary ''),('69131d51-8b86-4470-a07c-a51305df8782','61cab59a-456f-4bc2-b11c-4398c498dd12',_binary ''),('69131d51-8b86-4470-a07c-a51305df8782','69e1f2f9-5014-47df-b6aa-91ca814888df',_binary ''),('69131d51-8b86-4470-a07c-a51305df8782','9730d937-6ad4-4e39-a78c-176e16c88b8f',_binary '\0'),('69131d51-8b86-4470-a07c-a51305df8782','d2557dc6-b207-4785-9db3-e88e0eca290c',_binary '\0'),('69131d51-8b86-4470-a07c-a51305df8782','d8f588a9-7bb7-41be-ba22-d9b75e9a8195',_binary '\0'),('69131d51-8b86-4470-a07c-a51305df8782','daf2f7b7-f1c7-458f-8a62-d72cc891a82d',_binary ''),('77249ec3-5596-4d8b-a2d3-15604ca70de5','1d548a75-32d2-458d-96e5-772421f7c1bd',_binary ''),('77249ec3-5596-4d8b-a2d3-15604ca70de5','1f6b4061-797c-4caf-b130-c7ced3da55a7',_binary ''),('77249ec3-5596-4d8b-a2d3-15604ca70de5','21ac849d-f14e-4ecf-9e98-dc065603e167',_binary ''),('77249ec3-5596-4d8b-a2d3-15604ca70de5','a968f0db-2113-4e70-960f-3c2e1c1d3e94',_binary '\0'),('77249ec3-5596-4d8b-a2d3-15604ca70de5','bd2d9561-e102-45f0-a7c5-8fa07a8f925b',_binary ''),('77249ec3-5596-4d8b-a2d3-15604ca70de5','bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb',_binary ''),('77249ec3-5596-4d8b-a2d3-15604ca70de5','c6151be7-666a-487a-ad06-615fe9997983',_binary '\0'),('77249ec3-5596-4d8b-a2d3-15604ca70de5','d4b72e00-8775-47e0-8412-8cac6a2c3054',_binary '\0'),('77249ec3-5596-4d8b-a2d3-15604ca70de5','d7825fa7-20e1-43af-9ced-2a9d44117616',_binary '\0'),('8ae1bc8c-be2e-4b41-943c-63bd2aaf0e03','1fdf2898-fa16-457d-8d1b-89e86e0bef77',_binary ''),('8ae1bc8c-be2e-4b41-943c-63bd2aaf0e03','4b170f2c-e31b-4d03-8a2a-b514b444bfa6',_binary '\0'),('8ae1bc8c-be2e-4b41-943c-63bd2aaf0e03','5bbfcb16-0bcb-49e6-a25c-a2ac6c795864',_binary ''),('8ae1bc8c-be2e-4b41-943c-63bd2aaf0e03','61cab59a-456f-4bc2-b11c-4398c498dd12',_binary ''),('8ae1bc8c-be2e-4b41-943c-63bd2aaf0e03','69e1f2f9-5014-47df-b6aa-91ca814888df',_binary ''),('8ae1bc8c-be2e-4b41-943c-63bd2aaf0e03','9730d937-6ad4-4e39-a78c-176e16c88b8f',_binary '\0'),('8ae1bc8c-be2e-4b41-943c-63bd2aaf0e03','d2557dc6-b207-4785-9db3-e88e0eca290c',_binary '\0'),('8ae1bc8c-be2e-4b41-943c-63bd2aaf0e03','d8f588a9-7bb7-41be-ba22-d9b75e9a8195',_binary '\0'),('8ae1bc8c-be2e-4b41-943c-63bd2aaf0e03','daf2f7b7-f1c7-458f-8a62-d72cc891a82d',_binary ''),('bf810e04-c833-40e0-9170-b2a6ca33ce32','1d548a75-32d2-458d-96e5-772421f7c1bd',_binary ''),('bf810e04-c833-40e0-9170-b2a6ca33ce32','1f6b4061-797c-4caf-b130-c7ced3da55a7',_binary ''),('bf810e04-c833-40e0-9170-b2a6ca33ce32','21ac849d-f14e-4ecf-9e98-dc065603e167',_binary ''),('bf810e04-c833-40e0-9170-b2a6ca33ce32','a968f0db-2113-4e70-960f-3c2e1c1d3e94',_binary '\0'),('bf810e04-c833-40e0-9170-b2a6ca33ce32','bd2d9561-e102-45f0-a7c5-8fa07a8f925b',_binary ''),('bf810e04-c833-40e0-9170-b2a6ca33ce32','bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb',_binary ''),('bf810e04-c833-40e0-9170-b2a6ca33ce32','c6151be7-666a-487a-ad06-615fe9997983',_binary '\0'),('bf810e04-c833-40e0-9170-b2a6ca33ce32','d4b72e00-8775-47e0-8412-8cac6a2c3054',_binary '\0'),('bf810e04-c833-40e0-9170-b2a6ca33ce32','d7825fa7-20e1-43af-9ced-2a9d44117616',_binary '\0'),('e43e0012-146a-42a3-909a-59ac2a345d24','1d548a75-32d2-458d-96e5-772421f7c1bd',_binary ''),('e43e0012-146a-42a3-909a-59ac2a345d24','1f6b4061-797c-4caf-b130-c7ced3da55a7',_binary ''),('e43e0012-146a-42a3-909a-59ac2a345d24','21ac849d-f14e-4ecf-9e98-dc065603e167',_binary ''),('e43e0012-146a-42a3-909a-59ac2a345d24','a968f0db-2113-4e70-960f-3c2e1c1d3e94',_binary '\0'),('e43e0012-146a-42a3-909a-59ac2a345d24','bd2d9561-e102-45f0-a7c5-8fa07a8f925b',_binary ''),('e43e0012-146a-42a3-909a-59ac2a345d24','bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb',_binary ''),('e43e0012-146a-42a3-909a-59ac2a345d24','c6151be7-666a-487a-ad06-615fe9997983',_binary '\0'),('e43e0012-146a-42a3-909a-59ac2a345d24','d4b72e00-8775-47e0-8412-8cac6a2c3054',_binary '\0'),('e43e0012-146a-42a3-909a-59ac2a345d24','d7825fa7-20e1-43af-9ced-2a9d44117616',_binary '\0'),('e47088a1-3190-435b-a237-e4e0b50988d5','1fdf2898-fa16-457d-8d1b-89e86e0bef77',_binary ''),('e47088a1-3190-435b-a237-e4e0b50988d5','4b170f2c-e31b-4d03-8a2a-b514b444bfa6',_binary '\0'),('e47088a1-3190-435b-a237-e4e0b50988d5','5bbfcb16-0bcb-49e6-a25c-a2ac6c795864',_binary ''),('e47088a1-3190-435b-a237-e4e0b50988d5','61cab59a-456f-4bc2-b11c-4398c498dd12',_binary ''),('e47088a1-3190-435b-a237-e4e0b50988d5','69e1f2f9-5014-47df-b6aa-91ca814888df',_binary ''),('e47088a1-3190-435b-a237-e4e0b50988d5','9730d937-6ad4-4e39-a78c-176e16c88b8f',_binary '\0'),('e47088a1-3190-435b-a237-e4e0b50988d5','d2557dc6-b207-4785-9db3-e88e0eca290c',_binary '\0'),('e47088a1-3190-435b-a237-e4e0b50988d5','d8f588a9-7bb7-41be-ba22-d9b75e9a8195',_binary '\0'),('e47088a1-3190-435b-a237-e4e0b50988d5','daf2f7b7-f1c7-458f-8a62-d72cc891a82d',_binary ''),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03','1d548a75-32d2-458d-96e5-772421f7c1bd',_binary ''),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03','1f6b4061-797c-4caf-b130-c7ced3da55a7',_binary ''),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03','21ac849d-f14e-4ecf-9e98-dc065603e167',_binary ''),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03','a968f0db-2113-4e70-960f-3c2e1c1d3e94',_binary '\0'),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03','bd2d9561-e102-45f0-a7c5-8fa07a8f925b',_binary ''),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03','bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb',_binary ''),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03','c6151be7-666a-487a-ad06-615fe9997983',_binary '\0'),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03','d4b72e00-8775-47e0-8412-8cac6a2c3054',_binary '\0'),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03','d7825fa7-20e1-43af-9ced-2a9d44117616',_binary '\0');
/*!40000 ALTER TABLE `CLIENT_SCOPE_CLIENT` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_SCOPE_ROLE_MAPPING`
--

DROP TABLE IF EXISTS `CLIENT_SCOPE_ROLE_MAPPING`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_SCOPE_ROLE_MAPPING` (
  `SCOPE_ID` varchar(36) NOT NULL,
  `ROLE_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`SCOPE_ID`,`ROLE_ID`),
  KEY `IDX_CLSCOPE_ROLE` (`SCOPE_ID`),
  KEY `IDX_ROLE_CLSCOPE` (`ROLE_ID`),
  CONSTRAINT `FK_CL_SCOPE_RM_SCOPE` FOREIGN KEY (`SCOPE_ID`) REFERENCES `CLIENT_SCOPE` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_SCOPE_ROLE_MAPPING`
--

LOCK TABLES `CLIENT_SCOPE_ROLE_MAPPING` WRITE;
/*!40000 ALTER TABLE `CLIENT_SCOPE_ROLE_MAPPING` DISABLE KEYS */;
INSERT INTO `CLIENT_SCOPE_ROLE_MAPPING` VALUES ('c6151be7-666a-487a-ad06-615fe9997983','52a3415d-65a9-4314-8805-c85ca05b55d6'),('d8f588a9-7bb7-41be-ba22-d9b75e9a8195','cbc5dbe2-ac59-4b57-a641-387d94e759c6');
/*!40000 ALTER TABLE `CLIENT_SCOPE_ROLE_MAPPING` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_SESSION`
--

DROP TABLE IF EXISTS `CLIENT_SESSION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_SESSION` (
  `ID` varchar(36) NOT NULL,
  `CLIENT_ID` varchar(36) DEFAULT NULL,
  `REDIRECT_URI` varchar(255) DEFAULT NULL,
  `STATE` varchar(255) DEFAULT NULL,
  `TIMESTAMP` int DEFAULT NULL,
  `SESSION_ID` varchar(36) DEFAULT NULL,
  `AUTH_METHOD` varchar(255) DEFAULT NULL,
  `REALM_ID` varchar(255) DEFAULT NULL,
  `AUTH_USER_ID` varchar(36) DEFAULT NULL,
  `CURRENT_ACTION` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_CLIENT_SESSION_SESSION` (`SESSION_ID`),
  CONSTRAINT `FK_B4AO2VCVAT6UKAU74WBWTFQO1` FOREIGN KEY (`SESSION_ID`) REFERENCES `USER_SESSION` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_SESSION`
--

LOCK TABLES `CLIENT_SESSION` WRITE;
/*!40000 ALTER TABLE `CLIENT_SESSION` DISABLE KEYS */;
/*!40000 ALTER TABLE `CLIENT_SESSION` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_SESSION_AUTH_STATUS`
--

DROP TABLE IF EXISTS `CLIENT_SESSION_AUTH_STATUS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_SESSION_AUTH_STATUS` (
  `AUTHENTICATOR` varchar(36) NOT NULL,
  `STATUS` int DEFAULT NULL,
  `CLIENT_SESSION` varchar(36) NOT NULL,
  PRIMARY KEY (`CLIENT_SESSION`,`AUTHENTICATOR`),
  CONSTRAINT `AUTH_STATUS_CONSTRAINT` FOREIGN KEY (`CLIENT_SESSION`) REFERENCES `CLIENT_SESSION` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_SESSION_AUTH_STATUS`
--

LOCK TABLES `CLIENT_SESSION_AUTH_STATUS` WRITE;
/*!40000 ALTER TABLE `CLIENT_SESSION_AUTH_STATUS` DISABLE KEYS */;
/*!40000 ALTER TABLE `CLIENT_SESSION_AUTH_STATUS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_SESSION_NOTE`
--

DROP TABLE IF EXISTS `CLIENT_SESSION_NOTE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_SESSION_NOTE` (
  `NAME` varchar(255) NOT NULL,
  `VALUE` varchar(255) DEFAULT NULL,
  `CLIENT_SESSION` varchar(36) NOT NULL,
  PRIMARY KEY (`CLIENT_SESSION`,`NAME`),
  CONSTRAINT `FK5EDFB00FF51C2736` FOREIGN KEY (`CLIENT_SESSION`) REFERENCES `CLIENT_SESSION` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_SESSION_NOTE`
--

LOCK TABLES `CLIENT_SESSION_NOTE` WRITE;
/*!40000 ALTER TABLE `CLIENT_SESSION_NOTE` DISABLE KEYS */;
/*!40000 ALTER TABLE `CLIENT_SESSION_NOTE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_SESSION_PROT_MAPPER`
--

DROP TABLE IF EXISTS `CLIENT_SESSION_PROT_MAPPER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_SESSION_PROT_MAPPER` (
  `PROTOCOL_MAPPER_ID` varchar(36) NOT NULL,
  `CLIENT_SESSION` varchar(36) NOT NULL,
  PRIMARY KEY (`CLIENT_SESSION`,`PROTOCOL_MAPPER_ID`),
  CONSTRAINT `FK_33A8SGQW18I532811V7O2DK89` FOREIGN KEY (`CLIENT_SESSION`) REFERENCES `CLIENT_SESSION` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_SESSION_PROT_MAPPER`
--

LOCK TABLES `CLIENT_SESSION_PROT_MAPPER` WRITE;
/*!40000 ALTER TABLE `CLIENT_SESSION_PROT_MAPPER` DISABLE KEYS */;
/*!40000 ALTER TABLE `CLIENT_SESSION_PROT_MAPPER` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_SESSION_ROLE`
--

DROP TABLE IF EXISTS `CLIENT_SESSION_ROLE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_SESSION_ROLE` (
  `ROLE_ID` varchar(255) NOT NULL,
  `CLIENT_SESSION` varchar(36) NOT NULL,
  PRIMARY KEY (`CLIENT_SESSION`,`ROLE_ID`),
  CONSTRAINT `FK_11B7SGQW18I532811V7O2DV76` FOREIGN KEY (`CLIENT_SESSION`) REFERENCES `CLIENT_SESSION` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_SESSION_ROLE`
--

LOCK TABLES `CLIENT_SESSION_ROLE` WRITE;
/*!40000 ALTER TABLE `CLIENT_SESSION_ROLE` DISABLE KEYS */;
/*!40000 ALTER TABLE `CLIENT_SESSION_ROLE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CLIENT_USER_SESSION_NOTE`
--

DROP TABLE IF EXISTS `CLIENT_USER_SESSION_NOTE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CLIENT_USER_SESSION_NOTE` (
  `NAME` varchar(255) NOT NULL,
  `VALUE` text,
  `CLIENT_SESSION` varchar(36) NOT NULL,
  PRIMARY KEY (`CLIENT_SESSION`,`NAME`),
  CONSTRAINT `FK_CL_USR_SES_NOTE` FOREIGN KEY (`CLIENT_SESSION`) REFERENCES `CLIENT_SESSION` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CLIENT_USER_SESSION_NOTE`
--

LOCK TABLES `CLIENT_USER_SESSION_NOTE` WRITE;
/*!40000 ALTER TABLE `CLIENT_USER_SESSION_NOTE` DISABLE KEYS */;
/*!40000 ALTER TABLE `CLIENT_USER_SESSION_NOTE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `COMPONENT`
--

DROP TABLE IF EXISTS `COMPONENT`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMPONENT` (
  `ID` varchar(36) NOT NULL,
  `NAME` varchar(255) DEFAULT NULL,
  `PARENT_ID` varchar(36) DEFAULT NULL,
  `PROVIDER_ID` varchar(36) DEFAULT NULL,
  `PROVIDER_TYPE` varchar(255) DEFAULT NULL,
  `REALM_ID` varchar(36) DEFAULT NULL,
  `SUB_TYPE` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_COMPONENT_REALM` (`REALM_ID`),
  KEY `IDX_COMPONENT_PROVIDER_TYPE` (`PROVIDER_TYPE`),
  CONSTRAINT `FK_COMPONENT_REALM` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `COMPONENT`
--

LOCK TABLES `COMPONENT` WRITE;
/*!40000 ALTER TABLE `COMPONENT` DISABLE KEYS */;
INSERT INTO `COMPONENT` VALUES ('0577253c-f46f-4d6f-8a3e-b4ea2c760107','rsa-generated','WESkit','rsa-generated','org.keycloak.keys.KeyProvider','WESkit',NULL),('24b29579-2418-4d31-953f-3bd4dbec3639','Allowed Client Scopes','WESkit','allowed-client-templates','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','WESkit','authenticated'),('258e36b4-d37f-4d92-9fcd-09c94da22d6b','Trusted Hosts','WESkit','trusted-hosts','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','WESkit','anonymous'),('27cd2bd2-adfa-41bd-9723-45da11da91fd','hmac-generated','WESkit','hmac-generated','org.keycloak.keys.KeyProvider','WESkit',NULL),('2de8ef38-b645-44db-a1fe-b78ad2982e18','Allowed Protocol Mapper Types','WESkit','allowed-protocol-mappers','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','WESkit','anonymous'),('356cd0ab-6d7d-4f62-ba96-f23aa2d01cad','Consent Required','master','consent-required','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','master','anonymous'),('3af4c373-0cb4-440c-ade7-db81bed6efb6','Max Clients Limit','WESkit','max-clients','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','WESkit','anonymous'),('48184b27-6798-4dc3-a4fa-50b02cfafcf2','aes-generated','WESkit','aes-generated','org.keycloak.keys.KeyProvider','WESkit',NULL),('4c9093e9-bbab-4c11-ae21-92f3b0b18d70','Full Scope Disabled','master','scope','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','master','anonymous'),('5fdac0e3-acc8-4156-afb1-dde5e848cf41','Max Clients Limit','master','max-clients','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','master','anonymous'),('611d517f-0bfe-4e76-9d80-488f6bdc04a1','Allowed Client Scopes','WESkit','allowed-client-templates','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','WESkit','anonymous'),('8d02e11b-b161-4fdc-9a6c-9e5075d122bc','Allowed Protocol Mapper Types','master','allowed-protocol-mappers','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','master','anonymous'),('a037a972-cf0e-4894-ba44-ab8e24732b48','Allowed Protocol Mapper Types','WESkit','allowed-protocol-mappers','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','WESkit','authenticated'),('a81b9455-03f4-4022-966f-7d8b0ec7f135','fallback-HS256','master','hmac-generated','org.keycloak.keys.KeyProvider','master',NULL),('ba87d963-0ae4-47e0-9eeb-b303b477d3a3','Allowed Protocol Mapper Types','master','allowed-protocol-mappers','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','master','authenticated'),('c0a37bac-23da-47ba-a1ff-60cab751e4b7','Consent Required','WESkit','consent-required','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','WESkit','anonymous'),('cc0161a6-5388-4f6e-a558-0ecd0e9aa78a','Trusted Hosts','master','trusted-hosts','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','master','anonymous'),('ccc8527e-5140-4364-ae91-466156d10edd','Allowed Client Scopes','master','allowed-client-templates','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','master','authenticated'),('d01510f6-f43e-4904-9e95-ad6aa412bf92','Allowed Client Scopes','master','allowed-client-templates','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','master','anonymous'),('d5a7a7d1-fef4-4897-9102-9d46fdb0b112','fallback-RS256','master','rsa-generated','org.keycloak.keys.KeyProvider','master',NULL),('e602673c-8218-4d89-b780-1bb5b9288b10','Full Scope Disabled','WESkit','scope','org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy','WESkit','anonymous');
/*!40000 ALTER TABLE `COMPONENT` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `COMPONENT_CONFIG`
--

DROP TABLE IF EXISTS `COMPONENT_CONFIG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMPONENT_CONFIG` (
  `ID` varchar(36) NOT NULL,
  `COMPONENT_ID` varchar(36) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `VALUE` varchar(4000) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_COMPO_CONFIG_COMPO` (`COMPONENT_ID`),
  CONSTRAINT `FK_COMPONENT_CONFIG` FOREIGN KEY (`COMPONENT_ID`) REFERENCES `COMPONENT` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `COMPONENT_CONFIG`
--

LOCK TABLES `COMPONENT_CONFIG` WRITE;
/*!40000 ALTER TABLE `COMPONENT_CONFIG` DISABLE KEYS */;
INSERT INTO `COMPONENT_CONFIG` VALUES ('0128881d-85d0-4178-958f-e0d3cceaafe6','ba87d963-0ae4-47e0-9eeb-b303b477d3a3','allowed-protocol-mapper-types','oidc-address-mapper'),('04ac9174-3dba-4214-97cb-58298562af1b','d5a7a7d1-fef4-4897-9102-9d46fdb0b112','algorithm','RS256'),('079f2f4a-6430-406e-a278-a023ae1b3789','ba87d963-0ae4-47e0-9eeb-b303b477d3a3','allowed-protocol-mapper-types','oidc-usermodel-attribute-mapper'),('0fb649b4-dc3d-46f3-8cb7-42ac12c91673','a037a972-cf0e-4894-ba44-ab8e24732b48','allowed-protocol-mapper-types','saml-role-list-mapper'),('100760fd-9fea-466f-83fe-5ac46f2ca901','ba87d963-0ae4-47e0-9eeb-b303b477d3a3','allowed-protocol-mapper-types','saml-role-list-mapper'),('1308bea7-61c0-4889-ab0b-1fc0113f0604','48184b27-6798-4dc3-a4fa-50b02cfafcf2','secret','IUThShAzB1_2svSByArbAQ'),('1a940ab2-7a16-4aa1-87f5-a5a5358e3ac5','d5a7a7d1-fef4-4897-9102-9d46fdb0b112','priority','-100'),('1ab81053-be63-4338-920d-824b86c5bf5f','d5a7a7d1-fef4-4897-9102-9d46fdb0b112','certificate','MIICmzCCAYMCBgF31CwbijANBgkqhkiG9w0BAQsFADARMQ8wDQYDVQQDDAZtYXN0ZXIwHhcNMjEwMjI0MTMxMTM2WhcNMzEwMjI0MTMxMzE2WjARMQ8wDQYDVQQDDAZtYXN0ZXIwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCOLdXwTGLOHyusoM0AW+soOvcKcMhgtAGcJqZTai0SSnv8rUblaC49YaIXBJI5LxdT/b0e337iSxJbs0HS/tvP9JxuvVpY7pLQIfa6nBQIrIGrNamH0/dij28TYFILSL//6szJWvFYR4AZB0uJhujsgf2fhfYaC24IWOeqLZ19W0RHgyY96s0//U85i8qKpDycRIwHGLZhqv58u0E/K+34WeQlh9XgS6UygOgxMVwhqndevgmWBiXkwLbmerOedtu94y0ug2a6m28MPKkC0X+OWmzTQ5exY/7DEsjoBnkEivN4fEhCTxL+Nfz9LAmFSHnROMkOcXBldV8haeZCMQgzAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAEuMiGw8jvgz/YGpZrjNGdS3VeR4wiJDX+0g0RfyjhSO8xRGSKam7CXWl6hrgSTMrGL3SiZfVjnhKk5EmxL6p2UlakQPK/6Ug5smnKRGxfWzV3G2u+nWcOIQmSRDtzm16R2M3XvjrPRxVR5T4XovqgcVz6HCa2ZbVWt8mkUqjbZ3YOx26aAIRf+JPHqKEb1WcUSBO2p+ZIS517hUMhpKMS9ijM53qJyK59/EK+TeE1l42IFoGBDZt3pUoQDzZzU32xGRKIEvKiuMPyZTojfW6xMZIWcEduo3RtO/xCgLZUwpetTr3mAZU1zk5msdRpNErxrB/QBDSz3B77mVpu/dDo4='),('219272df-daa3-45e5-a801-dcdc6b740ba5','2de8ef38-b645-44db-a1fe-b78ad2982e18','allowed-protocol-mapper-types','oidc-full-name-mapper'),('25a3eb1b-0f9c-438c-99a8-ee612597a3b0','0577253c-f46f-4d6f-8a3e-b4ea2c760107','certificate','MIICmzCCAYMCBgF31ClKCzANBgkqhkiG9w0BAQsFADARMQ8wDQYDVQQDDAZXRVNraXQwHhcNMjEwMjI0MTMwODMxWhcNMzEwMjI0MTMxMDExWjARMQ8wDQYDVQQDDAZXRVNraXQwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCBJ0qTHuopEmuU7MwHlllWBuwn1W3sh9uGn+wvok/aP1Q3COJUbXnJ+woxBlBR7f6OrLZoyG5sG2yuIrHtcowVszi8gY1sZ4STNT4VcXop+WUnypoVeEFK9jYwBRH7tKe9z9ls9q5V8n9kba+SmhoXQzANtA8fmkzMWpVvfF/qvwugy0B7GjZKHGC8DxW+Ep7dau2IYHE7RTALB0mByei8uqUyvsas4OEeSR5wj7t66ydN/4MquU51i19mUsfIjw9I5NIGVqI5fowM1ehKpztktmqr3k1qHQlbMQRh+JzBV6zaDxSMc1BtbsNgSNl1DLbU6YH3Ct3XJjNUvnsKivR1AgMBAAEwDQYJKoZIhvcNAQELBQADggEBADwfxo2aXjZg36QMnKtiE+PxHJdRBK8VCafyn/IzRSX86c2esIDMid+x2PnXzm0ueG2lkYoDWCup8z7ZjDtQ918BkQrVn8/lIDLTHU6AuwZmrBL1HRMnHJIjAest2FS63uIoTuEsAeYOZVs/92U9TudRWykHAPDS+hnrawcd8CRuo2hFJkndxfEFJ6M+QnolPR5VaCs8PI3cebolFKupVeYsVsd/uh3dktWr0kaiOX+gI7pSIZMcq6J+iZE9PzTRYyKcBDInwMgsxGk8d9Ydfy4OQJsU55HiCRkp2HE+GNAUW3Sb9SRZEXPkq6/aiSrAqxEzxu0VEAC9HQpZZDmnQJo='),('2961d26f-9016-47c4-91dc-6d2be2fb1753','48184b27-6798-4dc3-a4fa-50b02cfafcf2','priority','100'),('3007e547-1e33-46b9-ab34-69f0810276e9','2de8ef38-b645-44db-a1fe-b78ad2982e18','allowed-protocol-mapper-types','saml-role-list-mapper'),('36c63501-db17-4b4f-a64b-bcc9a9096699','ba87d963-0ae4-47e0-9eeb-b303b477d3a3','allowed-protocol-mapper-types','oidc-full-name-mapper'),('3b6ad84c-e83c-491b-b41f-c614c81c9777','8d02e11b-b161-4fdc-9a6c-9e5075d122bc','allowed-protocol-mapper-types','oidc-usermodel-property-mapper'),('3c663307-6592-4cfe-9962-df114dbde948','2de8ef38-b645-44db-a1fe-b78ad2982e18','allowed-protocol-mapper-types','saml-user-property-mapper'),('3fd4ae16-f3d1-4d3c-8294-550cbb8c29ad','cc0161a6-5388-4f6e-a558-0ecd0e9aa78a','client-uris-must-match','true'),('43b01bed-994f-4b35-89bb-9f2a3c22f8d9','27cd2bd2-adfa-41bd-9723-45da11da91fd','priority','100'),('442db5cf-39ab-4920-9ea6-1d89dc5ae18a','0577253c-f46f-4d6f-8a3e-b4ea2c760107','priority','100'),('478b166b-2c7d-400f-94b5-ebc4aad04501','258e36b4-d37f-4d92-9fcd-09c94da22d6b','client-uris-must-match','true'),('4b599e38-4ef5-43b9-a127-3ebfe4a7c4ac','2de8ef38-b645-44db-a1fe-b78ad2982e18','allowed-protocol-mapper-types','oidc-address-mapper'),('5f62697c-aba0-4c56-abef-8dcb44ada717','8d02e11b-b161-4fdc-9a6c-9e5075d122bc','allowed-protocol-mapper-types','oidc-usermodel-attribute-mapper'),('5f66b231-5d8e-4658-bf4d-07d094b3b284','ba87d963-0ae4-47e0-9eeb-b303b477d3a3','allowed-protocol-mapper-types','oidc-usermodel-property-mapper'),('6a466cc8-ed20-4cc5-8b07-10a8dc12c11f','a037a972-cf0e-4894-ba44-ab8e24732b48','allowed-protocol-mapper-types','saml-user-property-mapper'),('6d94a2d8-7460-4586-9246-fdd959c4162f','24b29579-2418-4d31-953f-3bd4dbec3639','allow-default-scopes','true'),('6f2e094d-4595-4bb3-b1ae-574b7d929eee','2de8ef38-b645-44db-a1fe-b78ad2982e18','allowed-protocol-mapper-types','oidc-sha256-pairwise-sub-mapper'),('70ec44e5-353b-4a5f-a282-390f06517b80','8d02e11b-b161-4fdc-9a6c-9e5075d122bc','allowed-protocol-mapper-types','saml-role-list-mapper'),('744680e6-f777-4492-bae4-de6e2065ee72','a037a972-cf0e-4894-ba44-ab8e24732b48','allowed-protocol-mapper-types','oidc-usermodel-property-mapper'),('76fce4d9-057a-40f7-ae5e-032fbb27426e','ccc8527e-5140-4364-ae91-466156d10edd','allow-default-scopes','true'),('793b2ccb-2d73-4605-a2bf-2a363b403a0b','ba87d963-0ae4-47e0-9eeb-b303b477d3a3','allowed-protocol-mapper-types','saml-user-attribute-mapper'),('7969fa8a-5f44-4b20-bc72-e37337ec5fae','8d02e11b-b161-4fdc-9a6c-9e5075d122bc','allowed-protocol-mapper-types','oidc-sha256-pairwise-sub-mapper'),('7e2dc68a-f519-441a-9308-61a0d87fb919','a037a972-cf0e-4894-ba44-ab8e24732b48','allowed-protocol-mapper-types','saml-user-attribute-mapper'),('85fffcac-38ec-47ef-ba29-ea5bfd9e9880','a81b9455-03f4-4022-966f-7d8b0ec7f135','algorithm','HS256'),('8af5b77a-a2df-4744-859c-83a08fb1eac3','0577253c-f46f-4d6f-8a3e-b4ea2c760107','privateKey','MIIEowIBAAKCAQEAgSdKkx7qKRJrlOzMB5ZZVgbsJ9Vt7Ifbhp/sL6JP2j9UNwjiVG15yfsKMQZQUe3+jqy2aMhubBtsriKx7XKMFbM4vIGNbGeEkzU+FXF6KfllJ8qaFXhBSvY2MAUR+7Snvc/ZbPauVfJ/ZG2vkpoaF0MwDbQPH5pMzFqVb3xf6r8LoMtAexo2ShxgvA8VvhKe3WrtiGBxO0UwCwdJgcnovLqlMr7GrODhHkkecI+7eusnTf+DKrlOdYtfZlLHyI8PSOTSBlaiOX6MDNXoSqc7ZLZqq95Nah0JWzEEYficwVes2g8UjHNQbW7DYEjZdQy21OmB9wrd1yYzVL57Cor0dQIDAQABAoIBAEYxNoSSzqyXyEReFd0hx1fL11km0+EzTQnzrIeO7VsuA/UNLQS5ovE1MKrIRarhb/HWyCRWmjzDAuP5Ez57fMrmZrV8q4H5GMJws1cwHzbkxidEI03713CIM5cRil6EJo4wgniH8OPhMX9BZaSFgByYdWtdKsMANzDxIjo/HFoVyM+wqlVV2RSJTFKkSJK3AJAar/sRm7CFz487BNDiRtsPQVePmOub6zR5F7AtNztUM0tYkcHFXEwFxa2mT+/0wNPZHrxdX44eWlR6Kx9g15ru3oGc+fwmzm15S2duwDJ3NqLDHX6UJPNXoMNQievLua0i+tqHOxA+OVbacznLaYECgYEAvN5coINQDYU+Ta4IBlNX+RrHweEvPiDUqBwO3USPbVk7Ks/Fx1t0fZvUwWF2hSbOdE+bP/XCWepoVd+tA3SZc96dZoSjADutaPEZeLTTDyw15Xs+4Q1HgJkzQOu388hRIUXJxTgHPOH0NSAdZnxz3aB6CE7LDtecl8T54EcQc4UCgYEArw9MNifFdKo6dG4IPp3OPtfuiWgwyqt0p+yYK0tzm/AYvSMZTu5gE/xSUqvZQ2B+K4AjoC4r+AbRFsFA40oM3ByRxr814gyNPfCmv0vqADxO1K3JlluI4kRxtDguaCJFXo7ArBPwiwgPgZC7Gf0ruBf0T/lWLbtKk85Mt/FM+DECgYEAjCIoc+g6U23ThmtkBN193pRiNpZQKTbO0lTPKpmeGbIlVmSHCJ3w1unyd/FKsQzUDjSqqlA8fd6Qv3aQtomi+fforZIoJxogVkbdcVQpbY6OBtDlHLJvpRkGkFrVSAoPODLBvJUPubqlKW3EorAggAZ7xQJBY6fSxkEebawMpskCgYBWbDTxn1zJpahKBnAniXxiZfOq/jboNxDWPeU5qnwehb+Q0B0UbHYeJ7j0e0Y9Dwv6qb3svB6Uybi7hRhlnQ8QM0J8XbVaLVwlMgL/+ZhCGYPJVypoAjRnj+aaVAoE+rZIYi0YRpe/63DMRAk6YVQOBDVmre8vkIDWy0fwnz2iYQKBgC73H5R1dxBXRJbEvAufHruy77Y5CL1zdX3XaMC6wh1rRMhPmHmS2s7cTSpv7Jg0dma8S5lWy588/bg+YambqWxSvoVD+0gfdwdzzKNtbINh01yYHVrUhrcl5MmKfFaA92syBnZEHpTsl1MczPC7sjN8SZmHqJptNOibLZbTpc33'),('8d8152dd-32e1-4775-a19d-6c3dd76df2e1','258e36b4-d37f-4d92-9fcd-09c94da22d6b','host-sending-registration-request-must-match','true'),('92533c65-83f7-4a5d-889d-02b9191718a4','27cd2bd2-adfa-41bd-9723-45da11da91fd','algorithm','HS256'),('9430d653-adc7-4ff4-942b-482f23123fd4','611d517f-0bfe-4e76-9d80-488f6bdc04a1','allow-default-scopes','true'),('9fa10442-a1df-4ded-afef-d6a4c530b752','a81b9455-03f4-4022-966f-7d8b0ec7f135','kid','377ae806-e7d6-4127-a11a-1c6f8e3b0c31'),('a6c0e9ac-489e-462c-b420-f1ebfe68ed63','48184b27-6798-4dc3-a4fa-50b02cfafcf2','kid','20eb9d86-0bf3-4d1c-9fcb-3571d06f2a1f'),('a87d6277-bcdf-41de-9b6d-839ea391768d','2de8ef38-b645-44db-a1fe-b78ad2982e18','allowed-protocol-mapper-types','saml-user-attribute-mapper'),('ad5b6eb9-5099-4285-abdd-85e0763eb2aa','ba87d963-0ae4-47e0-9eeb-b303b477d3a3','allowed-protocol-mapper-types','oidc-sha256-pairwise-sub-mapper'),('b4bede28-67c1-4ebb-a7c6-dd3801ed44a5','8d02e11b-b161-4fdc-9a6c-9e5075d122bc','allowed-protocol-mapper-types','oidc-full-name-mapper'),('b723544b-26bc-4d9f-89d0-9d7883e8d80e','27cd2bd2-adfa-41bd-9723-45da11da91fd','secret','roAa5pAlR3ppS5S5xIGdUe3pJPVbMxgIUWUKd3a5daOjZXp_kcdoqPJ8ZjuDcFg_eIVCBOLzmsQ1ncx5XQ4U_w'),('b77b9f6a-c68a-43a4-97c7-e6653b67a0d5','a81b9455-03f4-4022-966f-7d8b0ec7f135','priority','-100'),('ba0312a2-b640-4abb-9bba-d3d3b8a7c53b','a037a972-cf0e-4894-ba44-ab8e24732b48','allowed-protocol-mapper-types','oidc-sha256-pairwise-sub-mapper'),('bd54f802-3dc2-458a-a405-6a9f5212365d','27cd2bd2-adfa-41bd-9723-45da11da91fd','kid','6b8b5282-bd69-4ce9-b431-776a47a1bc83'),('c856e518-b635-4a2a-92f8-48fbad9dea0e','8d02e11b-b161-4fdc-9a6c-9e5075d122bc','allowed-protocol-mapper-types','saml-user-property-mapper'),('c8601f44-98fb-4fad-bec4-918d53f74bd9','a81b9455-03f4-4022-966f-7d8b0ec7f135','secret','Bb5JhnDS4p-GFZ0wRFBNtkASf3vTTWPRRhlFRypNnQFRAs2s0HFCRxj63Medc4kMzMI9z55pfZYEYzOo1yzBiQ'),('cb59bad0-97a0-4909-950e-709b0f7a6aad','a037a972-cf0e-4894-ba44-ab8e24732b48','allowed-protocol-mapper-types','oidc-address-mapper'),('cf65fe8e-8df5-4a1e-a48f-b3bc02e977e4','2de8ef38-b645-44db-a1fe-b78ad2982e18','allowed-protocol-mapper-types','oidc-usermodel-attribute-mapper'),('dd628aab-18c4-41d4-9c52-806a03df4b61','5fdac0e3-acc8-4156-afb1-dde5e848cf41','max-clients','200'),('e80546eb-0bcb-4fd2-a7d0-7c1852cdb659','ba87d963-0ae4-47e0-9eeb-b303b477d3a3','allowed-protocol-mapper-types','saml-user-property-mapper'),('e85aebbe-f117-47bf-9d7f-f18f06bc29f7','d5a7a7d1-fef4-4897-9102-9d46fdb0b112','privateKey','MIIEpAIBAAKCAQEAji3V8Exizh8rrKDNAFvrKDr3CnDIYLQBnCamU2otEkp7/K1G5WguPWGiFwSSOS8XU/29Ht9+4ksSW7NB0v7bz/Scbr1aWO6S0CH2upwUCKyBqzWph9P3Yo9vE2BSC0i//+rMyVrxWEeAGQdLiYbo7IH9n4X2GgtuCFjnqi2dfVtER4MmPerNP/1POYvKiqQ8nESMBxi2Yar+fLtBPyvt+FnkJYfV4EulMoDoMTFcIap3Xr4JlgYl5MC25nqznnbbveMtLoNmuptvDDypAtF/jlps00OXsWP+wxLI6AZ5BIrzeHxIQk8S/jX8/SwJhUh50TjJDnFwZXVfIWnmQjEIMwIDAQABAoIBAGSWrQtLH4QwrVd+lEqyvVZDEVBDpqAz+gedmILfVW/hXoLPnJ7k7AHlNyYNx93JITn9BHX5LO2wqxZRZjp+sMkZiCsYr/jHIPs7bDFuBwZz9XFJj91W62jBjZYpySHOoHfQiH3UZ3dLbqdGb/ymg9f/x4262vhmKbyiGZRenVN31ie4JC2yMi6Kw/BV/jB5P/UezF0yXr6WMhUp7YF96mv1L5gxClitgx+2X4Yk3ndWBJy6WwiL2YTksHRiFUCVUH/v5gLa4hRDlGzrOulsytsfIgAniaz+QeExGlesbZKqa3aU9LcZkC20sJ084SSd24gjqR7TCRG7UfOVUWdWx7ECgYEAyWMiwEjUjAeaFfSILEFU7skr2INe8hmPvN0tyePpZhk/QmKfbKvWW4iSnNQvO4yoFJbsEGAInMcoHXX3FwJtUlgIf9ai7VUYhTJH2rynrIpscwNK4s7aUoRf1+wnsZRlthdHHwreW56xoO+iiYfmACpYEDY6ABJQp3oIUsjpBB8CgYEAtLxNKaTLV7W817PN/h9OkqPO2fFXWwpoCu7TwnL+WrgXwJLWBahcnqbXeT4K8ml0aWm7bQU7hzv5GqG3g4zck4+owQGE3B8xs9yKyXS1nyju7iqZuCO488r00uv0IOYiqoewT8m4QQuAFZcyVrzNWv9pHOu3ha1IJMsslp4E2W0CgYEAxTuTWFC74Zy8Ww5Po1Ak12wsxfL7tQ41yRmxc44EE1tcqi6exraQzLq4JGJnE+JQ50FcVzlGlg0zC49x/JYC7WeMg295yAjUZ/bzipXDfedgCVBLMlC2X6SHnZgK1A9rgefQXuWtGnwUqXKodBultbnC37XMHi/R0ARjTHi6Ra8CgYAGx1E1kKK3xW8xv+Kn91ChG1e0wOJ/3aINVuvGTT3Q9Tqe1GMGj0v5/1Pxjiwm72GYWojXC+0xo0QyhYI2gt/7ANZZds8e2mSo1Eq4R5JQR96+PAbL6zsSmbgY+RSM71S5hKFOPMiWV/IT3TncGvSwxweQOB8H+nnMN3qSo5aW+QKBgQCvzEVkoTaFHXmSNWmTp1r8KtLdUH81doLyTlacUzitNKYiNPcSffFO17sJ0aEbFKr687D1Wht0bgH/ToY694GanJKIJNHw55fpeVO4DI+lvOGQPEIYEPIh55kxGHrkpfuvBL35907FnAbaNxHEKiiJ9b4Nc+ivbc9n+lKwe3Gapw=='),('e874d1f9-7f77-4808-a446-5fee890b6ae5','8d02e11b-b161-4fdc-9a6c-9e5075d122bc','allowed-protocol-mapper-types','saml-user-attribute-mapper'),('e972cde4-b410-4af8-8d4e-94d6036f9a2f','2de8ef38-b645-44db-a1fe-b78ad2982e18','allowed-protocol-mapper-types','oidc-usermodel-property-mapper'),('ec36c05e-e756-4456-85a1-8345facd2afa','3af4c373-0cb4-440c-ade7-db81bed6efb6','max-clients','200'),('ec572ae2-f584-4435-a064-a614ae758019','d01510f6-f43e-4904-9e95-ad6aa412bf92','allow-default-scopes','true'),('ee533e23-85fd-4c9d-8e88-47279d7e8566','a037a972-cf0e-4894-ba44-ab8e24732b48','allowed-protocol-mapper-types','oidc-full-name-mapper'),('f45c2880-1507-4f16-8693-a7b14a15286e','cc0161a6-5388-4f6e-a558-0ecd0e9aa78a','host-sending-registration-request-must-match','true'),('f7433014-ac2f-4c76-b679-089fc06a12d2','a037a972-cf0e-4894-ba44-ab8e24732b48','allowed-protocol-mapper-types','oidc-usermodel-attribute-mapper'),('f8164412-ff44-4529-8e2f-19ac25bac5c7','8d02e11b-b161-4fdc-9a6c-9e5075d122bc','allowed-protocol-mapper-types','oidc-address-mapper');
/*!40000 ALTER TABLE `COMPONENT_CONFIG` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `COMPOSITE_ROLE`
--

DROP TABLE IF EXISTS `COMPOSITE_ROLE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMPOSITE_ROLE` (
  `COMPOSITE` varchar(36) NOT NULL,
  `CHILD_ROLE` varchar(36) NOT NULL,
  PRIMARY KEY (`COMPOSITE`,`CHILD_ROLE`),
  KEY `IDX_COMPOSITE` (`COMPOSITE`),
  KEY `IDX_COMPOSITE_CHILD` (`CHILD_ROLE`),
  CONSTRAINT `FK_A63WVEKFTU8JO1PNJ81E7MCE2` FOREIGN KEY (`COMPOSITE`) REFERENCES `KEYCLOAK_ROLE` (`ID`),
  CONSTRAINT `FK_GR7THLLB9LU8Q4VQA4524JJY8` FOREIGN KEY (`CHILD_ROLE`) REFERENCES `KEYCLOAK_ROLE` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `COMPOSITE_ROLE`
--

LOCK TABLES `COMPOSITE_ROLE` WRITE;
/*!40000 ALTER TABLE `COMPOSITE_ROLE` DISABLE KEYS */;
INSERT INTO `COMPOSITE_ROLE` VALUES ('248a3f39-6dfe-422f-8c29-70c6669842fc','7fb99f4a-94c8-4888-987a-77b7dc255a30'),('2f449425-83d6-45a4-8814-04ed95b38fc0','39c4c0b3-ab8b-4479-be78-273b73992aa5'),('46cc8442-0314-4294-93eb-463e6a821bba','3b6d5695-9dd8-44cd-bba7-8db9f71b6f2f'),('4e7561b4-c79f-4d09-ba7f-a04b19a8b6cf','c3424f59-cc83-4d26-9839-86552a1cd03b'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','06f41222-5675-4a54-b953-421944c02923'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','1f25214f-98b1-4fb6-8ccf-c1480cbb8d35'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','2f449425-83d6-45a4-8814-04ed95b38fc0'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','35518ac8-8630-4b11-8005-e2ce0dd3a39c'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','39c4c0b3-ab8b-4479-be78-273b73992aa5'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','3b7b8cde-8644-4767-b8a2-efcaf0b809f3'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','4408e590-d9bb-411b-86d5-56e9e6417409'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','448fbe8c-3ffb-4dce-888c-a39dd187c4a5'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','572afd3d-87ca-4e56-8adf-7e3b0fe01d93'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','67358233-cc50-4565-b094-bab9d8a5ccd1'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','7972d87f-9237-48c3-94c9-cdc64d1305c8'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','8932ca33-75ab-4a41-b915-d0e368a30c5c'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','c9143bcc-c2ab-45e9-9434-496669091ac5'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','ca651a58-d1e1-436f-8aa0-295e305c9df2'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','dfa5c730-cf74-4eaa-93c6-f3566f177edc'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','eccd5ee8-068c-4a06-aed4-b5098bb78f50'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','ecef566e-72b5-477c-a1ef-5d4adb540cc4'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','fbde0c90-661c-4c6a-bd4c-67414d97536a'),('9c8169aa-b379-409b-bbe3-42592be27747','1328a8ef-2469-4c83-afba-8d96f2e93a28'),('9c8169aa-b379-409b-bbe3-42592be27747','1aab2464-0a06-4a68-bb9d-9a625c2e156e'),('9c8169aa-b379-409b-bbe3-42592be27747','27483a2d-95b9-4636-b920-de432ef02565'),('9c8169aa-b379-409b-bbe3-42592be27747','2df93e5a-7e08-459e-a1c0-4ecfc6ae00e4'),('9c8169aa-b379-409b-bbe3-42592be27747','2e60536d-4ee4-47cf-8d19-4f5c844777f6'),('9c8169aa-b379-409b-bbe3-42592be27747','47457aeb-a463-489e-b7d7-fcfd0e21363a'),('9c8169aa-b379-409b-bbe3-42592be27747','4e7561b4-c79f-4d09-ba7f-a04b19a8b6cf'),('9c8169aa-b379-409b-bbe3-42592be27747','4efe6faa-afd2-4690-98e2-4b2579adc59e'),('9c8169aa-b379-409b-bbe3-42592be27747','51f32f82-e980-4711-8655-6735c76ac53e'),('9c8169aa-b379-409b-bbe3-42592be27747','57420870-c874-4c4f-896f-bc17dc807fb1'),('9c8169aa-b379-409b-bbe3-42592be27747','6aeb41c8-8cd5-4bc7-b1ff-680579fdd828'),('9c8169aa-b379-409b-bbe3-42592be27747','6b3dccf1-7b9c-40b3-988a-10b2179928de'),('9c8169aa-b379-409b-bbe3-42592be27747','6c15817c-1196-487a-be12-c976b2d1b0cf'),('9c8169aa-b379-409b-bbe3-42592be27747','6cc9a54c-c82b-403f-bf4f-49679e6b8e53'),('9c8169aa-b379-409b-bbe3-42592be27747','6d540935-0f0f-4e77-b138-62338d49be17'),('9c8169aa-b379-409b-bbe3-42592be27747','6d9ce5c4-e378-416b-ac64-257a69617f82'),('9c8169aa-b379-409b-bbe3-42592be27747','7b3f7c39-8476-44b8-8bab-9f2fa2ed6295'),('9c8169aa-b379-409b-bbe3-42592be27747','88a8bbe2-97f2-49d6-af00-60b540d73fcf'),('9c8169aa-b379-409b-bbe3-42592be27747','9a31d20b-e9aa-4983-8465-b94ee9fb3b79'),('9c8169aa-b379-409b-bbe3-42592be27747','9e1c7db9-8233-4c8f-bc6e-b3820d98d642'),('9c8169aa-b379-409b-bbe3-42592be27747','a1583b65-4e81-495c-a968-c163fe412d1c'),('9c8169aa-b379-409b-bbe3-42592be27747','b48f8fd3-34b9-4321-ae27-5a071e889238'),('9c8169aa-b379-409b-bbe3-42592be27747','b5570588-5cba-455a-97a7-2f2c8939a044'),('9c8169aa-b379-409b-bbe3-42592be27747','b6e22a8b-860f-4805-a291-d8ae6d3c1878'),('9c8169aa-b379-409b-bbe3-42592be27747','bb90e6ad-005d-4711-a399-55c4730dca1a'),('9c8169aa-b379-409b-bbe3-42592be27747','bebfe83d-f732-4aa6-a3f8-421d3f2ec346'),('9c8169aa-b379-409b-bbe3-42592be27747','c3424f59-cc83-4d26-9839-86552a1cd03b'),('9c8169aa-b379-409b-bbe3-42592be27747','c3c522fb-be42-49d7-924d-72df2fa9b7ae'),('9c8169aa-b379-409b-bbe3-42592be27747','c40b393e-e3eb-4e08-b764-d05f692b3817'),('9c8169aa-b379-409b-bbe3-42592be27747','c8d9813c-3240-404a-a976-92917ff894a7'),('9c8169aa-b379-409b-bbe3-42592be27747','d09037a6-8d92-48d0-968b-e05fb0cb7282'),('9c8169aa-b379-409b-bbe3-42592be27747','d7c862d5-179c-4fd5-a116-6e8bf84fd94c'),('9c8169aa-b379-409b-bbe3-42592be27747','dc60a653-a1c6-44cb-abe8-e8db215ef0f8'),('9c8169aa-b379-409b-bbe3-42592be27747','dff6c1e5-d410-4680-a6d4-d420fa3dc329'),('9c8169aa-b379-409b-bbe3-42592be27747','e3c3bc13-bb35-46a7-a295-d35acf568419'),('9c8169aa-b379-409b-bbe3-42592be27747','f31579ab-a1b5-444f-9678-d1496dec385b'),('9c8169aa-b379-409b-bbe3-42592be27747','f909efa7-c95d-4afd-ba47-3c8d4d4dd960'),('9e1c7db9-8233-4c8f-bc6e-b3820d98d642','d09037a6-8d92-48d0-968b-e05fb0cb7282'),('9fe0f5ad-7ef3-4cd5-b216-9fc0e4021bf4','7a7d7dc3-3c1a-4ed1-888a-935478758892'),('bebfe83d-f732-4aa6-a3f8-421d3f2ec346','2df93e5a-7e08-459e-a1c0-4ecfc6ae00e4'),('bebfe83d-f732-4aa6-a3f8-421d3f2ec346','51f32f82-e980-4711-8655-6735c76ac53e'),('d7c862d5-179c-4fd5-a116-6e8bf84fd94c','9a31d20b-e9aa-4983-8465-b94ee9fb3b79'),('d7c862d5-179c-4fd5-a116-6e8bf84fd94c','a1583b65-4e81-495c-a968-c163fe412d1c'),('dfa5c730-cf74-4eaa-93c6-f3566f177edc','448fbe8c-3ffb-4dce-888c-a39dd187c4a5'),('dfa5c730-cf74-4eaa-93c6-f3566f177edc','572afd3d-87ca-4e56-8adf-7e3b0fe01d93'),('f96d9c1d-253f-4e51-86fb-844b2cdc84f4','b0bf3bf5-ad75-4eca-939a-fcfcab9ab018');
/*!40000 ALTER TABLE `COMPOSITE_ROLE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CREDENTIAL`
--

DROP TABLE IF EXISTS `CREDENTIAL`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CREDENTIAL` (
  `ID` varchar(36) NOT NULL,
  `SALT` tinyblob,
  `TYPE` varchar(255) DEFAULT NULL,
  `USER_ID` varchar(36) DEFAULT NULL,
  `CREATED_DATE` bigint DEFAULT NULL,
  `USER_LABEL` varchar(255) DEFAULT NULL,
  `SECRET_DATA` longtext,
  `CREDENTIAL_DATA` longtext,
  `PRIORITY` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_USER_CREDENTIAL` (`USER_ID`),
  CONSTRAINT `FK_PFYR0GLASQYL0DEI3KL69R6V0` FOREIGN KEY (`USER_ID`) REFERENCES `USER_ENTITY` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CREDENTIAL`
--

LOCK TABLES `CREDENTIAL` WRITE;
/*!40000 ALTER TABLE `CREDENTIAL` DISABLE KEYS */;
INSERT INTO `CREDENTIAL` VALUES ('6cdbacf7-15a1-4991-9b72-a0fc22df24b6',NULL,'password','b00fd985-a834-4863-9106-11aec150eecd',1614172462099,NULL,'{\"value\":\"reTlu+BNZQKdNi3Z0K0tBBYAmFVSfcZaB9OWC6vwTz+1DudV9T0DTdNYrqfd2L6aEHYxHe/+8VKpdkIebooS4Q==\",\"salt\":\"8bnsN9b3eu4OKbnDu5lJSA==\",\"additionalParameters\":{}}','{\"hashIterations\":27500,\"algorithm\":\"pbkdf2-sha256\",\"additionalParameters\":{}}',10),('6ee7452e-916a-444b-a737-84039241ec43',NULL,'password','dba63a01-c02a-4fdc-96ee-17c88a1023e3',1614172212163,NULL,'{\"value\":\"2lJsWxVYbeL+5t6sAwdPeBYWkcX6hhq7HRuUh5WlFBHLV0n9ah16h8fnwbJWIU8yIyMBL13sbSqlDViddwBcmA==\",\"salt\":\"J4RxnEf8CdSozT5USftBrw==\",\"additionalParameters\":{}}','{\"hashIterations\":27500,\"algorithm\":\"pbkdf2-sha256\",\"additionalParameters\":{}}',10),('7c8d5626-5103-4e75-8ff8-899abb9d39d2',NULL,'password','8f5ad792-5fbd-4c9d-b956-86513b92b971',1614940021295,NULL,'{\"value\":\"hhctkBx5eGnvO5s79WlA5+kgfKHsibOmr6zF95KEdLyZfQwArUl3o2DumwQ51jW+8EiwEsPObc50y7fd431dew==\",\"salt\":\"Kbv4AJ4XKlUSgW0plIO6Yg==\",\"additionalParameters\":{}}','{\"hashIterations\":27500,\"algorithm\":\"pbkdf2-sha256\",\"additionalParameters\":{}}',10),('f805b282-4fd9-448b-9e27-55325db07eb9',NULL,'password','6bd12400-6fc4-402c-9180-83bddbc30526',1614173030089,NULL,'{\"value\":\"YYKgv2JxbhuX6Kct+nkwACpzGDXbrzU4S8fXa0TSh1fL6sfBqk3MuOuRuVeR0o77Hr88bWF+BRYDZn109A8dYw==\",\"salt\":\"Vnba9R0Is2ySHWaXqQUBBg==\",\"additionalParameters\":{}}','{\"hashIterations\":27500,\"algorithm\":\"pbkdf2-sha256\",\"additionalParameters\":{}}',10);
/*!40000 ALTER TABLE `CREDENTIAL` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DATABASECHANGELOG`
--

DROP TABLE IF EXISTS `DATABASECHANGELOG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DATABASECHANGELOG` (
  `ID` varchar(255) NOT NULL,
  `AUTHOR` varchar(255) NOT NULL,
  `FILENAME` varchar(255) NOT NULL,
  `DATEEXECUTED` datetime NOT NULL,
  `ORDEREXECUTED` int NOT NULL,
  `EXECTYPE` varchar(10) NOT NULL,
  `MD5SUM` varchar(35) DEFAULT NULL,
  `DESCRIPTION` varchar(255) DEFAULT NULL,
  `COMMENTS` varchar(255) DEFAULT NULL,
  `TAG` varchar(255) DEFAULT NULL,
  `LIQUIBASE` varchar(20) DEFAULT NULL,
  `CONTEXTS` varchar(255) DEFAULT NULL,
  `LABELS` varchar(255) DEFAULT NULL,
  `DEPLOYMENT_ID` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DATABASECHANGELOG`
--

LOCK TABLES `DATABASECHANGELOG` WRITE;
/*!40000 ALTER TABLE `DATABASECHANGELOG` DISABLE KEYS */;
INSERT INTO `DATABASECHANGELOG` VALUES ('1.0.0.Final-KEYCLOAK-5461','sthorger@redhat.com','META-INF/jpa-changelog-1.0.0.Final.xml','2021-02-24 13:09:37',1,'EXECUTED','7:4e70412f24a3f382c82183742ec79317','createTable tableName=APPLICATION_DEFAULT_ROLES; createTable tableName=CLIENT; createTable tableName=CLIENT_SESSION; createTable tableName=CLIENT_SESSION_ROLE; createTable tableName=COMPOSITE_ROLE; createTable tableName=CREDENTIAL; createTable tab...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.0.0.Final-KEYCLOAK-5461','sthorger@redhat.com','META-INF/db2-jpa-changelog-1.0.0.Final.xml','2021-02-24 13:09:37',2,'MARK_RAN','7:cb16724583e9675711801c6875114f28','createTable tableName=APPLICATION_DEFAULT_ROLES; createTable tableName=CLIENT; createTable tableName=CLIENT_SESSION; createTable tableName=CLIENT_SESSION_ROLE; createTable tableName=COMPOSITE_ROLE; createTable tableName=CREDENTIAL; createTable tab...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.1.0.Beta1','sthorger@redhat.com','META-INF/jpa-changelog-1.1.0.Beta1.xml','2021-02-24 13:09:37',3,'EXECUTED','7:0310eb8ba07cec616460794d42ade0fa','delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION; createTable tableName=CLIENT_ATTRIBUTES; createTable tableName=CLIENT_SESSION_NOTE; createTable tableName=APP_NODE_REGISTRATIONS; addColumn table...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.1.0.Final','sthorger@redhat.com','META-INF/jpa-changelog-1.1.0.Final.xml','2021-02-24 13:09:37',4,'EXECUTED','7:5d25857e708c3233ef4439df1f93f012','renameColumn newColumnName=EVENT_TIME, oldColumnName=TIME, tableName=EVENT_ENTITY','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.2.0.Beta1','psilva@redhat.com','META-INF/jpa-changelog-1.2.0.Beta1.xml','2021-02-24 13:09:39',5,'EXECUTED','7:c7a54a1041d58eb3817a4a883b4d4e84','delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION; createTable tableName=PROTOCOL_MAPPER; createTable tableName=PROTOCOL_MAPPER_CONFIG; createTable tableName=...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.2.0.Beta1','psilva@redhat.com','META-INF/db2-jpa-changelog-1.2.0.Beta1.xml','2021-02-24 13:09:39',6,'MARK_RAN','7:2e01012df20974c1c2a605ef8afe25b7','delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION; createTable tableName=PROTOCOL_MAPPER; createTable tableName=PROTOCOL_MAPPER_CONFIG; createTable tableName=...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.2.0.RC1','bburke@redhat.com','META-INF/jpa-changelog-1.2.0.CR1.xml','2021-02-24 13:09:41',7,'EXECUTED','7:0f08df48468428e0f30ee59a8ec01a41','delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete tableName=USER_SESSION; createTable tableName=MIGRATION_MODEL; createTable tableName=IDENTITY_P...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.2.0.RC1','bburke@redhat.com','META-INF/db2-jpa-changelog-1.2.0.CR1.xml','2021-02-24 13:09:41',8,'MARK_RAN','7:a77ea2ad226b345e7d689d366f185c8c','delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete tableName=USER_SESSION; createTable tableName=MIGRATION_MODEL; createTable tableName=IDENTITY_P...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.2.0.Final','keycloak','META-INF/jpa-changelog-1.2.0.Final.xml','2021-02-24 13:09:41',9,'EXECUTED','7:a3377a2059aefbf3b90ebb4c4cc8e2ab','update tableName=CLIENT; update tableName=CLIENT; update tableName=CLIENT','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.3.0','bburke@redhat.com','META-INF/jpa-changelog-1.3.0.xml','2021-02-24 13:09:43',10,'EXECUTED','7:04c1dbedc2aa3e9756d1a1668e003451','delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_PROT_MAPPER; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete tableName=USER_SESSION; createTable tableName=ADMI...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.4.0','bburke@redhat.com','META-INF/jpa-changelog-1.4.0.xml','2021-02-24 13:09:44',11,'EXECUTED','7:36ef39ed560ad07062d956db861042ba','delete tableName=CLIENT_SESSION_AUTH_STATUS; delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_PROT_MAPPER; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete table...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.4.0','bburke@redhat.com','META-INF/db2-jpa-changelog-1.4.0.xml','2021-02-24 13:09:44',12,'MARK_RAN','7:d909180b2530479a716d3f9c9eaea3d7','delete tableName=CLIENT_SESSION_AUTH_STATUS; delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_PROT_MAPPER; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete table...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.5.0','bburke@redhat.com','META-INF/jpa-changelog-1.5.0.xml','2021-02-24 13:09:44',13,'EXECUTED','7:cf12b04b79bea5152f165eb41f3955f6','delete tableName=CLIENT_SESSION_AUTH_STATUS; delete tableName=CLIENT_SESSION_ROLE; delete tableName=CLIENT_SESSION_PROT_MAPPER; delete tableName=CLIENT_SESSION_NOTE; delete tableName=CLIENT_SESSION; delete tableName=USER_SESSION_NOTE; delete table...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.6.1_from15','mposolda@redhat.com','META-INF/jpa-changelog-1.6.1.xml','2021-02-24 13:09:44',14,'EXECUTED','7:7e32c8f05c755e8675764e7d5f514509','addColumn tableName=REALM; addColumn tableName=KEYCLOAK_ROLE; addColumn tableName=CLIENT; createTable tableName=OFFLINE_USER_SESSION; createTable tableName=OFFLINE_CLIENT_SESSION; addPrimaryKey constraintName=CONSTRAINT_OFFL_US_SES_PK2, tableName=...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.6.1_from16-pre','mposolda@redhat.com','META-INF/jpa-changelog-1.6.1.xml','2021-02-24 13:09:44',15,'MARK_RAN','7:980ba23cc0ec39cab731ce903dd01291','delete tableName=OFFLINE_CLIENT_SESSION; delete tableName=OFFLINE_USER_SESSION','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.6.1_from16','mposolda@redhat.com','META-INF/jpa-changelog-1.6.1.xml','2021-02-24 13:09:44',16,'MARK_RAN','7:2fa220758991285312eb84f3b4ff5336','dropPrimaryKey constraintName=CONSTRAINT_OFFLINE_US_SES_PK, tableName=OFFLINE_USER_SESSION; dropPrimaryKey constraintName=CONSTRAINT_OFFLINE_CL_SES_PK, tableName=OFFLINE_CLIENT_SESSION; addColumn tableName=OFFLINE_USER_SESSION; update tableName=OF...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.6.1','mposolda@redhat.com','META-INF/jpa-changelog-1.6.1.xml','2021-02-24 13:09:44',17,'EXECUTED','7:d41d8cd98f00b204e9800998ecf8427e','empty','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.7.0','bburke@redhat.com','META-INF/jpa-changelog-1.7.0.xml','2021-02-24 13:09:46',18,'EXECUTED','7:91ace540896df890cc00a0490ee52bbc','createTable tableName=KEYCLOAK_GROUP; createTable tableName=GROUP_ROLE_MAPPING; createTable tableName=GROUP_ATTRIBUTE; createTable tableName=USER_GROUP_MEMBERSHIP; createTable tableName=REALM_DEFAULT_GROUPS; addColumn tableName=IDENTITY_PROVIDER; ...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.8.0','mposolda@redhat.com','META-INF/jpa-changelog-1.8.0.xml','2021-02-24 13:09:47',19,'EXECUTED','7:c31d1646dfa2618a9335c00e07f89f24','addColumn tableName=IDENTITY_PROVIDER; createTable tableName=CLIENT_TEMPLATE; createTable tableName=CLIENT_TEMPLATE_ATTRIBUTES; createTable tableName=TEMPLATE_SCOPE_MAPPING; dropNotNullConstraint columnName=CLIENT_ID, tableName=PROTOCOL_MAPPER; ad...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.8.0-2','keycloak','META-INF/jpa-changelog-1.8.0.xml','2021-02-24 13:09:47',20,'EXECUTED','7:df8bc21027a4f7cbbb01f6344e89ce07','dropDefaultValue columnName=ALGORITHM, tableName=CREDENTIAL; update tableName=CREDENTIAL','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.8.0','mposolda@redhat.com','META-INF/db2-jpa-changelog-1.8.0.xml','2021-02-24 13:09:47',21,'MARK_RAN','7:f987971fe6b37d963bc95fee2b27f8df','addColumn tableName=IDENTITY_PROVIDER; createTable tableName=CLIENT_TEMPLATE; createTable tableName=CLIENT_TEMPLATE_ATTRIBUTES; createTable tableName=TEMPLATE_SCOPE_MAPPING; dropNotNullConstraint columnName=CLIENT_ID, tableName=PROTOCOL_MAPPER; ad...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.8.0-2','keycloak','META-INF/db2-jpa-changelog-1.8.0.xml','2021-02-24 13:09:47',22,'MARK_RAN','7:df8bc21027a4f7cbbb01f6344e89ce07','dropDefaultValue columnName=ALGORITHM, tableName=CREDENTIAL; update tableName=CREDENTIAL','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.9.0','mposolda@redhat.com','META-INF/jpa-changelog-1.9.0.xml','2021-02-24 13:09:47',23,'EXECUTED','7:ed2dc7f799d19ac452cbcda56c929e47','update tableName=REALM; update tableName=REALM; update tableName=REALM; update tableName=REALM; update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=REALM; update tableName=REALM; customChange; dr...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.9.1','keycloak','META-INF/jpa-changelog-1.9.1.xml','2021-02-24 13:09:47',24,'EXECUTED','7:80b5db88a5dda36ece5f235be8757615','modifyDataType columnName=PRIVATE_KEY, tableName=REALM; modifyDataType columnName=PUBLIC_KEY, tableName=REALM; modifyDataType columnName=CERTIFICATE, tableName=REALM','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.9.1','keycloak','META-INF/db2-jpa-changelog-1.9.1.xml','2021-02-24 13:09:47',25,'MARK_RAN','7:1437310ed1305a9b93f8848f301726ce','modifyDataType columnName=PRIVATE_KEY, tableName=REALM; modifyDataType columnName=CERTIFICATE, tableName=REALM','',NULL,'3.5.4',NULL,NULL,'4172172991'),('1.9.2','keycloak','META-INF/jpa-changelog-1.9.2.xml','2021-02-24 13:09:48',26,'EXECUTED','7:b82ffb34850fa0836be16deefc6a87c4','createIndex indexName=IDX_USER_EMAIL, tableName=USER_ENTITY; createIndex indexName=IDX_USER_ROLE_MAPPING, tableName=USER_ROLE_MAPPING; createIndex indexName=IDX_USER_GROUP_MAPPING, tableName=USER_GROUP_MEMBERSHIP; createIndex indexName=IDX_USER_CO...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('authz-2.0.0','psilva@redhat.com','META-INF/jpa-changelog-authz-2.0.0.xml','2021-02-24 13:09:49',27,'EXECUTED','7:9cc98082921330d8d9266decdd4bd658','createTable tableName=RESOURCE_SERVER; addPrimaryKey constraintName=CONSTRAINT_FARS, tableName=RESOURCE_SERVER; addUniqueConstraint constraintName=UK_AU8TT6T700S9V50BU18WS5HA6, tableName=RESOURCE_SERVER; createTable tableName=RESOURCE_SERVER_RESOU...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('authz-2.5.1','psilva@redhat.com','META-INF/jpa-changelog-authz-2.5.1.xml','2021-02-24 13:09:49',28,'EXECUTED','7:03d64aeed9cb52b969bd30a7ac0db57e','update tableName=RESOURCE_SERVER_POLICY','',NULL,'3.5.4',NULL,NULL,'4172172991'),('2.1.0-KEYCLOAK-5461','bburke@redhat.com','META-INF/jpa-changelog-2.1.0.xml','2021-02-24 13:09:50',29,'EXECUTED','7:f1f9fd8710399d725b780f463c6b21cd','createTable tableName=BROKER_LINK; createTable tableName=FED_USER_ATTRIBUTE; createTable tableName=FED_USER_CONSENT; createTable tableName=FED_USER_CONSENT_ROLE; createTable tableName=FED_USER_CONSENT_PROT_MAPPER; createTable tableName=FED_USER_CR...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('2.2.0','bburke@redhat.com','META-INF/jpa-changelog-2.2.0.xml','2021-02-24 13:09:50',30,'EXECUTED','7:53188c3eb1107546e6f765835705b6c1','addColumn tableName=ADMIN_EVENT_ENTITY; createTable tableName=CREDENTIAL_ATTRIBUTE; createTable tableName=FED_CREDENTIAL_ATTRIBUTE; modifyDataType columnName=VALUE, tableName=CREDENTIAL; addForeignKeyConstraint baseTableName=FED_CREDENTIAL_ATTRIBU...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('2.3.0','bburke@redhat.com','META-INF/jpa-changelog-2.3.0.xml','2021-02-24 13:09:51',31,'EXECUTED','7:d6e6f3bc57a0c5586737d1351725d4d4','createTable tableName=FEDERATED_USER; addPrimaryKey constraintName=CONSTR_FEDERATED_USER, tableName=FEDERATED_USER; dropDefaultValue columnName=TOTP, tableName=USER_ENTITY; dropColumn columnName=TOTP, tableName=USER_ENTITY; addColumn tableName=IDE...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('2.4.0','bburke@redhat.com','META-INF/jpa-changelog-2.4.0.xml','2021-02-24 13:09:51',32,'EXECUTED','7:454d604fbd755d9df3fd9c6329043aa5','customChange','',NULL,'3.5.4',NULL,NULL,'4172172991'),('2.5.0','bburke@redhat.com','META-INF/jpa-changelog-2.5.0.xml','2021-02-24 13:09:51',33,'EXECUTED','7:57e98a3077e29caf562f7dbf80c72600','customChange; modifyDataType columnName=USER_ID, tableName=OFFLINE_USER_SESSION','',NULL,'3.5.4',NULL,NULL,'4172172991'),('2.5.0-unicode-oracle','hmlnarik@redhat.com','META-INF/jpa-changelog-2.5.0.xml','2021-02-24 13:09:51',34,'MARK_RAN','7:e4c7e8f2256210aee71ddc42f538b57a','modifyDataType columnName=DESCRIPTION, tableName=AUTHENTICATION_FLOW; modifyDataType columnName=DESCRIPTION, tableName=CLIENT_TEMPLATE; modifyDataType columnName=DESCRIPTION, tableName=RESOURCE_SERVER_POLICY; modifyDataType columnName=DESCRIPTION,...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('2.5.0-unicode-other-dbs','hmlnarik@redhat.com','META-INF/jpa-changelog-2.5.0.xml','2021-02-24 13:09:53',35,'EXECUTED','7:09a43c97e49bc626460480aa1379b522','modifyDataType columnName=DESCRIPTION, tableName=AUTHENTICATION_FLOW; modifyDataType columnName=DESCRIPTION, tableName=CLIENT_TEMPLATE; modifyDataType columnName=DESCRIPTION, tableName=RESOURCE_SERVER_POLICY; modifyDataType columnName=DESCRIPTION,...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('2.5.0-duplicate-email-support','slawomir@dabek.name','META-INF/jpa-changelog-2.5.0.xml','2021-02-24 13:09:53',36,'EXECUTED','7:26bfc7c74fefa9126f2ce702fb775553','addColumn tableName=REALM','',NULL,'3.5.4',NULL,NULL,'4172172991'),('2.5.0-unique-group-names','hmlnarik@redhat.com','META-INF/jpa-changelog-2.5.0.xml','2021-02-24 13:09:53',37,'EXECUTED','7:a161e2ae671a9020fff61e996a207377','addUniqueConstraint constraintName=SIBLING_NAMES, tableName=KEYCLOAK_GROUP','',NULL,'3.5.4',NULL,NULL,'4172172991'),('2.5.1','bburke@redhat.com','META-INF/jpa-changelog-2.5.1.xml','2021-02-24 13:09:53',38,'EXECUTED','7:37fc1781855ac5388c494f1442b3f717','addColumn tableName=FED_USER_CONSENT','',NULL,'3.5.4',NULL,NULL,'4172172991'),('3.0.0','bburke@redhat.com','META-INF/jpa-changelog-3.0.0.xml','2021-02-24 13:09:53',39,'EXECUTED','7:13a27db0dae6049541136adad7261d27','addColumn tableName=IDENTITY_PROVIDER','',NULL,'3.5.4',NULL,NULL,'4172172991'),('3.2.0-fix','keycloak','META-INF/jpa-changelog-3.2.0.xml','2021-02-24 13:09:53',40,'MARK_RAN','7:550300617e3b59e8af3a6294df8248a3','addNotNullConstraint columnName=REALM_ID, tableName=CLIENT_INITIAL_ACCESS','',NULL,'3.5.4',NULL,NULL,'4172172991'),('3.2.0-fix-with-keycloak-5416','keycloak','META-INF/jpa-changelog-3.2.0.xml','2021-02-24 13:09:53',41,'MARK_RAN','7:e3a9482b8931481dc2772a5c07c44f17','dropIndex indexName=IDX_CLIENT_INIT_ACC_REALM, tableName=CLIENT_INITIAL_ACCESS; addNotNullConstraint columnName=REALM_ID, tableName=CLIENT_INITIAL_ACCESS; createIndex indexName=IDX_CLIENT_INIT_ACC_REALM, tableName=CLIENT_INITIAL_ACCESS','',NULL,'3.5.4',NULL,NULL,'4172172991'),('3.2.0-fix-offline-sessions','hmlnarik','META-INF/jpa-changelog-3.2.0.xml','2021-02-24 13:09:53',42,'EXECUTED','7:72b07d85a2677cb257edb02b408f332d','customChange','',NULL,'3.5.4',NULL,NULL,'4172172991'),('3.2.0-fixed','keycloak','META-INF/jpa-changelog-3.2.0.xml','2021-02-24 13:09:55',43,'EXECUTED','7:a72a7858967bd414835d19e04d880312','addColumn tableName=REALM; dropPrimaryKey constraintName=CONSTRAINT_OFFL_CL_SES_PK2, tableName=OFFLINE_CLIENT_SESSION; dropColumn columnName=CLIENT_SESSION_ID, tableName=OFFLINE_CLIENT_SESSION; addPrimaryKey constraintName=CONSTRAINT_OFFL_CL_SES_P...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('3.3.0','keycloak','META-INF/jpa-changelog-3.3.0.xml','2021-02-24 13:09:55',44,'EXECUTED','7:94edff7cf9ce179e7e85f0cd78a3cf2c','addColumn tableName=USER_ENTITY','',NULL,'3.5.4',NULL,NULL,'4172172991'),('authz-3.4.0.CR1-resource-server-pk-change-part1','glavoie@gmail.com','META-INF/jpa-changelog-authz-3.4.0.CR1.xml','2021-02-24 13:09:55',45,'EXECUTED','7:6a48ce645a3525488a90fbf76adf3bb3','addColumn tableName=RESOURCE_SERVER_POLICY; addColumn tableName=RESOURCE_SERVER_RESOURCE; addColumn tableName=RESOURCE_SERVER_SCOPE','',NULL,'3.5.4',NULL,NULL,'4172172991'),('authz-3.4.0.CR1-resource-server-pk-change-part2-KEYCLOAK-6095','hmlnarik@redhat.com','META-INF/jpa-changelog-authz-3.4.0.CR1.xml','2021-02-24 13:09:55',46,'EXECUTED','7:e64b5dcea7db06077c6e57d3b9e5ca14','customChange','',NULL,'3.5.4',NULL,NULL,'4172172991'),('authz-3.4.0.CR1-resource-server-pk-change-part3-fixed','glavoie@gmail.com','META-INF/jpa-changelog-authz-3.4.0.CR1.xml','2021-02-24 13:09:55',47,'MARK_RAN','7:fd8cf02498f8b1e72496a20afc75178c','dropIndex indexName=IDX_RES_SERV_POL_RES_SERV, tableName=RESOURCE_SERVER_POLICY; dropIndex indexName=IDX_RES_SRV_RES_RES_SRV, tableName=RESOURCE_SERVER_RESOURCE; dropIndex indexName=IDX_RES_SRV_SCOPE_RES_SRV, tableName=RESOURCE_SERVER_SCOPE','',NULL,'3.5.4',NULL,NULL,'4172172991'),('authz-3.4.0.CR1-resource-server-pk-change-part3-fixed-nodropindex','glavoie@gmail.com','META-INF/jpa-changelog-authz-3.4.0.CR1.xml','2021-02-24 13:09:56',48,'EXECUTED','7:542794f25aa2b1fbabb7e577d6646319','addNotNullConstraint columnName=RESOURCE_SERVER_CLIENT_ID, tableName=RESOURCE_SERVER_POLICY; addNotNullConstraint columnName=RESOURCE_SERVER_CLIENT_ID, tableName=RESOURCE_SERVER_RESOURCE; addNotNullConstraint columnName=RESOURCE_SERVER_CLIENT_ID, ...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('authn-3.4.0.CR1-refresh-token-max-reuse','glavoie@gmail.com','META-INF/jpa-changelog-authz-3.4.0.CR1.xml','2021-02-24 13:09:56',49,'EXECUTED','7:edad604c882df12f74941dac3cc6d650','addColumn tableName=REALM','',NULL,'3.5.4',NULL,NULL,'4172172991'),('3.4.0','keycloak','META-INF/jpa-changelog-3.4.0.xml','2021-02-24 13:09:57',50,'EXECUTED','7:0f88b78b7b46480eb92690cbf5e44900','addPrimaryKey constraintName=CONSTRAINT_REALM_DEFAULT_ROLES, tableName=REALM_DEFAULT_ROLES; addPrimaryKey constraintName=CONSTRAINT_COMPOSITE_ROLE, tableName=COMPOSITE_ROLE; addPrimaryKey constraintName=CONSTR_REALM_DEFAULT_GROUPS, tableName=REALM...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('3.4.0-KEYCLOAK-5230','hmlnarik@redhat.com','META-INF/jpa-changelog-3.4.0.xml','2021-02-24 13:09:58',51,'EXECUTED','7:d560e43982611d936457c327f872dd59','createIndex indexName=IDX_FU_ATTRIBUTE, tableName=FED_USER_ATTRIBUTE; createIndex indexName=IDX_FU_CONSENT, tableName=FED_USER_CONSENT; createIndex indexName=IDX_FU_CONSENT_RU, tableName=FED_USER_CONSENT; createIndex indexName=IDX_FU_CREDENTIAL, t...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('3.4.1','psilva@redhat.com','META-INF/jpa-changelog-3.4.1.xml','2021-02-24 13:09:58',52,'EXECUTED','7:c155566c42b4d14ef07059ec3b3bbd8e','modifyDataType columnName=VALUE, tableName=CLIENT_ATTRIBUTES','',NULL,'3.5.4',NULL,NULL,'4172172991'),('3.4.2','keycloak','META-INF/jpa-changelog-3.4.2.xml','2021-02-24 13:09:58',53,'EXECUTED','7:b40376581f12d70f3c89ba8ddf5b7dea','update tableName=REALM','',NULL,'3.5.4',NULL,NULL,'4172172991'),('3.4.2-KEYCLOAK-5172','mkanis@redhat.com','META-INF/jpa-changelog-3.4.2.xml','2021-02-24 13:09:58',54,'EXECUTED','7:a1132cc395f7b95b3646146c2e38f168','update tableName=CLIENT','',NULL,'3.5.4',NULL,NULL,'4172172991'),('4.0.0-KEYCLOAK-6335','bburke@redhat.com','META-INF/jpa-changelog-4.0.0.xml','2021-02-24 13:09:58',55,'EXECUTED','7:d8dc5d89c789105cfa7ca0e82cba60af','createTable tableName=CLIENT_AUTH_FLOW_BINDINGS; addPrimaryKey constraintName=C_CLI_FLOW_BIND, tableName=CLIENT_AUTH_FLOW_BINDINGS','',NULL,'3.5.4',NULL,NULL,'4172172991'),('4.0.0-CLEANUP-UNUSED-TABLE','bburke@redhat.com','META-INF/jpa-changelog-4.0.0.xml','2021-02-24 13:09:58',56,'EXECUTED','7:7822e0165097182e8f653c35517656a3','dropTable tableName=CLIENT_IDENTITY_PROV_MAPPING','',NULL,'3.5.4',NULL,NULL,'4172172991'),('4.0.0-KEYCLOAK-6228','bburke@redhat.com','META-INF/jpa-changelog-4.0.0.xml','2021-02-24 13:09:58',57,'EXECUTED','7:c6538c29b9c9a08f9e9ea2de5c2b6375','dropUniqueConstraint constraintName=UK_JKUWUVD56ONTGSUHOGM8UEWRT, tableName=USER_CONSENT; dropNotNullConstraint columnName=CLIENT_ID, tableName=USER_CONSENT; addColumn tableName=USER_CONSENT; addUniqueConstraint constraintName=UK_JKUWUVD56ONTGSUHO...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('4.0.0-KEYCLOAK-5579-fixed','mposolda@redhat.com','META-INF/jpa-changelog-4.0.0.xml','2021-02-24 13:10:01',58,'EXECUTED','7:6d4893e36de22369cf73bcb051ded875','dropForeignKeyConstraint baseTableName=CLIENT_TEMPLATE_ATTRIBUTES, constraintName=FK_CL_TEMPL_ATTR_TEMPL; renameTable newTableName=CLIENT_SCOPE_ATTRIBUTES, oldTableName=CLIENT_TEMPLATE_ATTRIBUTES; renameColumn newColumnName=SCOPE_ID, oldColumnName...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('authz-4.0.0.CR1','psilva@redhat.com','META-INF/jpa-changelog-authz-4.0.0.CR1.xml','2021-02-24 13:10:01',59,'EXECUTED','7:57960fc0b0f0dd0563ea6f8b2e4a1707','createTable tableName=RESOURCE_SERVER_PERM_TICKET; addPrimaryKey constraintName=CONSTRAINT_FAPMT, tableName=RESOURCE_SERVER_PERM_TICKET; addForeignKeyConstraint baseTableName=RESOURCE_SERVER_PERM_TICKET, constraintName=FK_FRSRHO213XCX4WNKOG82SSPMT...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('authz-4.0.0.Beta3','psilva@redhat.com','META-INF/jpa-changelog-authz-4.0.0.Beta3.xml','2021-02-24 13:10:02',60,'EXECUTED','7:2b4b8bff39944c7097977cc18dbceb3b','addColumn tableName=RESOURCE_SERVER_POLICY; addColumn tableName=RESOURCE_SERVER_PERM_TICKET; addForeignKeyConstraint baseTableName=RESOURCE_SERVER_PERM_TICKET, constraintName=FK_FRSRPO2128CX4WNKOG82SSRFY, referencedTableName=RESOURCE_SERVER_POLICY','',NULL,'3.5.4',NULL,NULL,'4172172991'),('authz-4.2.0.Final','mhajas@redhat.com','META-INF/jpa-changelog-authz-4.2.0.Final.xml','2021-02-24 13:10:02',61,'EXECUTED','7:2aa42a964c59cd5b8ca9822340ba33a8','createTable tableName=RESOURCE_URIS; addForeignKeyConstraint baseTableName=RESOURCE_URIS, constraintName=FK_RESOURCE_SERVER_URIS, referencedTableName=RESOURCE_SERVER_RESOURCE; customChange; dropColumn columnName=URI, tableName=RESOURCE_SERVER_RESO...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('authz-4.2.0.Final-KEYCLOAK-9944','hmlnarik@redhat.com','META-INF/jpa-changelog-authz-4.2.0.Final.xml','2021-02-24 13:10:02',62,'EXECUTED','7:9ac9e58545479929ba23f4a3087a0346','addPrimaryKey constraintName=CONSTRAINT_RESOUR_URIS_PK, tableName=RESOURCE_URIS','',NULL,'3.5.4',NULL,NULL,'4172172991'),('4.2.0-KEYCLOAK-6313','wadahiro@gmail.com','META-INF/jpa-changelog-4.2.0.xml','2021-02-24 13:10:02',63,'EXECUTED','7:14d407c35bc4fe1976867756bcea0c36','addColumn tableName=REQUIRED_ACTION_PROVIDER','',NULL,'3.5.4',NULL,NULL,'4172172991'),('4.3.0-KEYCLOAK-7984','wadahiro@gmail.com','META-INF/jpa-changelog-4.3.0.xml','2021-02-24 13:10:02',64,'EXECUTED','7:241a8030c748c8548e346adee548fa93','update tableName=REQUIRED_ACTION_PROVIDER','',NULL,'3.5.4',NULL,NULL,'4172172991'),('4.6.0-KEYCLOAK-7950','psilva@redhat.com','META-INF/jpa-changelog-4.6.0.xml','2021-02-24 13:10:02',65,'EXECUTED','7:7d3182f65a34fcc61e8d23def037dc3f','update tableName=RESOURCE_SERVER_RESOURCE','',NULL,'3.5.4',NULL,NULL,'4172172991'),('4.6.0-KEYCLOAK-8377','keycloak','META-INF/jpa-changelog-4.6.0.xml','2021-02-24 13:10:02',66,'EXECUTED','7:b30039e00a0b9715d430d1b0636728fa','createTable tableName=ROLE_ATTRIBUTE; addPrimaryKey constraintName=CONSTRAINT_ROLE_ATTRIBUTE_PK, tableName=ROLE_ATTRIBUTE; addForeignKeyConstraint baseTableName=ROLE_ATTRIBUTE, constraintName=FK_ROLE_ATTRIBUTE_ID, referencedTableName=KEYCLOAK_ROLE...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('4.6.0-KEYCLOAK-8555','gideonray@gmail.com','META-INF/jpa-changelog-4.6.0.xml','2021-02-24 13:10:02',67,'EXECUTED','7:3797315ca61d531780f8e6f82f258159','createIndex indexName=IDX_COMPONENT_PROVIDER_TYPE, tableName=COMPONENT','',NULL,'3.5.4',NULL,NULL,'4172172991'),('4.7.0-KEYCLOAK-1267','sguilhen@redhat.com','META-INF/jpa-changelog-4.7.0.xml','2021-02-24 13:10:02',68,'EXECUTED','7:c7aa4c8d9573500c2d347c1941ff0301','addColumn tableName=REALM','',NULL,'3.5.4',NULL,NULL,'4172172991'),('4.7.0-KEYCLOAK-7275','keycloak','META-INF/jpa-changelog-4.7.0.xml','2021-02-24 13:10:02',69,'EXECUTED','7:b207faee394fc074a442ecd42185a5dd','renameColumn newColumnName=CREATED_ON, oldColumnName=LAST_SESSION_REFRESH, tableName=OFFLINE_USER_SESSION; addNotNullConstraint columnName=CREATED_ON, tableName=OFFLINE_USER_SESSION; addColumn tableName=OFFLINE_USER_SESSION; customChange; createIn...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('4.8.0-KEYCLOAK-8835','sguilhen@redhat.com','META-INF/jpa-changelog-4.8.0.xml','2021-02-24 13:10:02',70,'EXECUTED','7:ab9a9762faaba4ddfa35514b212c4922','addNotNullConstraint columnName=SSO_MAX_LIFESPAN_REMEMBER_ME, tableName=REALM; addNotNullConstraint columnName=SSO_IDLE_TIMEOUT_REMEMBER_ME, tableName=REALM','',NULL,'3.5.4',NULL,NULL,'4172172991'),('authz-7.0.0-KEYCLOAK-10443','psilva@redhat.com','META-INF/jpa-changelog-authz-7.0.0.xml','2021-02-24 13:10:02',71,'EXECUTED','7:b9710f74515a6ccb51b72dc0d19df8c4','addColumn tableName=RESOURCE_SERVER','',NULL,'3.5.4',NULL,NULL,'4172172991'),('8.0.0-adding-credential-columns','keycloak','META-INF/jpa-changelog-8.0.0.xml','2021-02-24 13:10:03',72,'EXECUTED','7:ec9707ae4d4f0b7452fee20128083879','addColumn tableName=CREDENTIAL; addColumn tableName=FED_USER_CREDENTIAL','',NULL,'3.5.4',NULL,NULL,'4172172991'),('8.0.0-updating-credential-data-not-oracle','keycloak','META-INF/jpa-changelog-8.0.0.xml','2021-02-24 13:10:03',73,'EXECUTED','7:03b3f4b264c3c68ba082250a80b74216','update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=FED_USER_CREDENTIAL; update tableName=FED_USER_CREDENTIAL; update tableName=FED_USER_CREDENTIAL','',NULL,'3.5.4',NULL,NULL,'4172172991'),('8.0.0-updating-credential-data-oracle','keycloak','META-INF/jpa-changelog-8.0.0.xml','2021-02-24 13:10:03',74,'MARK_RAN','7:64c5728f5ca1f5aa4392217701c4fe23','update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=CREDENTIAL; update tableName=FED_USER_CREDENTIAL; update tableName=FED_USER_CREDENTIAL; update tableName=FED_USER_CREDENTIAL','',NULL,'3.5.4',NULL,NULL,'4172172991'),('8.0.0-credential-cleanup-fixed','keycloak','META-INF/jpa-changelog-8.0.0.xml','2021-02-24 13:10:04',75,'EXECUTED','7:b48da8c11a3d83ddd6b7d0c8c2219345','dropDefaultValue columnName=COUNTER, tableName=CREDENTIAL; dropDefaultValue columnName=DIGITS, tableName=CREDENTIAL; dropDefaultValue columnName=PERIOD, tableName=CREDENTIAL; dropDefaultValue columnName=ALGORITHM, tableName=CREDENTIAL; dropColumn ...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('8.0.0-resource-tag-support','keycloak','META-INF/jpa-changelog-8.0.0.xml','2021-02-24 13:10:04',76,'EXECUTED','7:a73379915c23bfad3e8f5c6d5c0aa4bd','addColumn tableName=MIGRATION_MODEL; createIndex indexName=IDX_UPDATE_TIME, tableName=MIGRATION_MODEL','',NULL,'3.5.4',NULL,NULL,'4172172991'),('9.0.0-always-display-client','keycloak','META-INF/jpa-changelog-9.0.0.xml','2021-02-24 13:10:04',77,'EXECUTED','7:39e0073779aba192646291aa2332493d','addColumn tableName=CLIENT','',NULL,'3.5.4',NULL,NULL,'4172172991'),('9.0.0-drop-constraints-for-column-increase','keycloak','META-INF/jpa-changelog-9.0.0.xml','2021-02-24 13:10:04',78,'MARK_RAN','7:81f87368f00450799b4bf42ea0b3ec34','dropUniqueConstraint constraintName=UK_FRSR6T700S9V50BU18WS5PMT, tableName=RESOURCE_SERVER_PERM_TICKET; dropUniqueConstraint constraintName=UK_FRSR6T700S9V50BU18WS5HA6, tableName=RESOURCE_SERVER_RESOURCE; dropPrimaryKey constraintName=CONSTRAINT_O...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('9.0.0-increase-column-size-federated-fk','keycloak','META-INF/jpa-changelog-9.0.0.xml','2021-02-24 13:10:04',79,'EXECUTED','7:20b37422abb9fb6571c618148f013a15','modifyDataType columnName=CLIENT_ID, tableName=FED_USER_CONSENT; modifyDataType columnName=CLIENT_REALM_CONSTRAINT, tableName=KEYCLOAK_ROLE; modifyDataType columnName=OWNER, tableName=RESOURCE_SERVER_POLICY; modifyDataType columnName=CLIENT_ID, ta...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('9.0.0-recreate-constraints-after-column-increase','keycloak','META-INF/jpa-changelog-9.0.0.xml','2021-02-24 13:10:04',80,'MARK_RAN','7:1970bb6cfb5ee800736b95ad3fb3c78a','addNotNullConstraint columnName=CLIENT_ID, tableName=OFFLINE_CLIENT_SESSION; addNotNullConstraint columnName=OWNER, tableName=RESOURCE_SERVER_PERM_TICKET; addNotNullConstraint columnName=REQUESTER, tableName=RESOURCE_SERVER_PERM_TICKET; addNotNull...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('9.0.1-add-index-to-client.client_id','keycloak','META-INF/jpa-changelog-9.0.1.xml','2021-02-24 13:10:04',81,'EXECUTED','7:45d9b25fc3b455d522d8dcc10a0f4c80','createIndex indexName=IDX_CLIENT_ID, tableName=CLIENT','',NULL,'3.5.4',NULL,NULL,'4172172991'),('9.0.1-KEYCLOAK-12579-drop-constraints','keycloak','META-INF/jpa-changelog-9.0.1.xml','2021-02-24 13:10:04',82,'MARK_RAN','7:890ae73712bc187a66c2813a724d037f','dropUniqueConstraint constraintName=SIBLING_NAMES, tableName=KEYCLOAK_GROUP','',NULL,'3.5.4',NULL,NULL,'4172172991'),('9.0.1-KEYCLOAK-12579-add-not-null-constraint','keycloak','META-INF/jpa-changelog-9.0.1.xml','2021-02-24 13:10:05',83,'EXECUTED','7:0a211980d27fafe3ff50d19a3a29b538','addNotNullConstraint columnName=PARENT_GROUP, tableName=KEYCLOAK_GROUP','',NULL,'3.5.4',NULL,NULL,'4172172991'),('9.0.1-KEYCLOAK-12579-recreate-constraints','keycloak','META-INF/jpa-changelog-9.0.1.xml','2021-02-24 13:10:05',84,'MARK_RAN','7:a161e2ae671a9020fff61e996a207377','addUniqueConstraint constraintName=SIBLING_NAMES, tableName=KEYCLOAK_GROUP','',NULL,'3.5.4',NULL,NULL,'4172172991'),('9.0.1-add-index-to-events','keycloak','META-INF/jpa-changelog-9.0.1.xml','2021-02-24 13:10:05',85,'EXECUTED','7:01c49302201bdf815b0a18d1f98a55dc','createIndex indexName=IDX_EVENT_TIME, tableName=EVENT_ENTITY','',NULL,'3.5.4',NULL,NULL,'4172172991'),('map-remove-ri','keycloak','META-INF/jpa-changelog-11.0.0.xml','2021-02-24 13:10:05',86,'EXECUTED','7:3dace6b144c11f53f1ad2c0361279b86','dropForeignKeyConstraint baseTableName=REALM, constraintName=FK_TRAF444KK6QRKMS7N56AIWQ5Y; dropForeignKeyConstraint baseTableName=KEYCLOAK_ROLE, constraintName=FK_KJHO5LE2C0RAL09FL8CM9WFW9','',NULL,'3.5.4',NULL,NULL,'4172172991'),('map-remove-ri','keycloak','META-INF/jpa-changelog-12.0.0.xml','2021-02-24 13:10:05',87,'EXECUTED','7:578d0b92077eaf2ab95ad0ec087aa903','dropForeignKeyConstraint baseTableName=REALM_DEFAULT_GROUPS, constraintName=FK_DEF_GROUPS_GROUP; dropForeignKeyConstraint baseTableName=REALM_DEFAULT_ROLES, constraintName=FK_H4WPD7W4HSOOLNI3H0SW7BTJE; dropForeignKeyConstraint baseTableName=CLIENT...','',NULL,'3.5.4',NULL,NULL,'4172172991'),('12.1.0-add-realm-localization-table','keycloak','META-INF/jpa-changelog-12.0.0.xml','2021-02-24 13:10:05',88,'EXECUTED','7:c95abe90d962c57a09ecaee57972835d','createTable tableName=REALM_LOCALIZATIONS; addPrimaryKey tableName=REALM_LOCALIZATIONS','',NULL,'3.5.4',NULL,NULL,'4172172991');
/*!40000 ALTER TABLE `DATABASECHANGELOG` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DATABASECHANGELOGLOCK`
--

DROP TABLE IF EXISTS `DATABASECHANGELOGLOCK`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DATABASECHANGELOGLOCK` (
  `ID` int NOT NULL,
  `LOCKED` bit(1) NOT NULL,
  `LOCKGRANTED` datetime DEFAULT NULL,
  `LOCKEDBY` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DATABASECHANGELOGLOCK`
--

LOCK TABLES `DATABASECHANGELOGLOCK` WRITE;
/*!40000 ALTER TABLE `DATABASECHANGELOGLOCK` DISABLE KEYS */;
INSERT INTO `DATABASECHANGELOGLOCK` VALUES (1,_binary '\0',NULL,NULL),(1000,_binary '\0',NULL,NULL),(1001,_binary '\0',NULL,NULL);
/*!40000 ALTER TABLE `DATABASECHANGELOGLOCK` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DEFAULT_CLIENT_SCOPE`
--

DROP TABLE IF EXISTS `DEFAULT_CLIENT_SCOPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DEFAULT_CLIENT_SCOPE` (
  `REALM_ID` varchar(36) NOT NULL,
  `SCOPE_ID` varchar(36) NOT NULL,
  `DEFAULT_SCOPE` bit(1) NOT NULL DEFAULT b'0',
  PRIMARY KEY (`REALM_ID`,`SCOPE_ID`),
  KEY `IDX_DEFCLS_REALM` (`REALM_ID`),
  KEY `IDX_DEFCLS_SCOPE` (`SCOPE_ID`),
  CONSTRAINT `FK_R_DEF_CLI_SCOPE_REALM` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`),
  CONSTRAINT `FK_R_DEF_CLI_SCOPE_SCOPE` FOREIGN KEY (`SCOPE_ID`) REFERENCES `CLIENT_SCOPE` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DEFAULT_CLIENT_SCOPE`
--

LOCK TABLES `DEFAULT_CLIENT_SCOPE` WRITE;
/*!40000 ALTER TABLE `DEFAULT_CLIENT_SCOPE` DISABLE KEYS */;
INSERT INTO `DEFAULT_CLIENT_SCOPE` VALUES ('master','1fdf2898-fa16-457d-8d1b-89e86e0bef77',_binary ''),('master','4b170f2c-e31b-4d03-8a2a-b514b444bfa6',_binary '\0'),('master','5bbfcb16-0bcb-49e6-a25c-a2ac6c795864',_binary ''),('master','61cab59a-456f-4bc2-b11c-4398c498dd12',_binary ''),('master','69e1f2f9-5014-47df-b6aa-91ca814888df',_binary ''),('master','9730d937-6ad4-4e39-a78c-176e16c88b8f',_binary '\0'),('master','d2557dc6-b207-4785-9db3-e88e0eca290c',_binary '\0'),('master','d8f588a9-7bb7-41be-ba22-d9b75e9a8195',_binary '\0'),('master','daf2f7b7-f1c7-458f-8a62-d72cc891a82d',_binary ''),('WESkit','1d548a75-32d2-458d-96e5-772421f7c1bd',_binary ''),('WESkit','1f6b4061-797c-4caf-b130-c7ced3da55a7',_binary ''),('WESkit','21ac849d-f14e-4ecf-9e98-dc065603e167',_binary ''),('WESkit','a968f0db-2113-4e70-960f-3c2e1c1d3e94',_binary '\0'),('WESkit','bd2d9561-e102-45f0-a7c5-8fa07a8f925b',_binary ''),('WESkit','bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb',_binary ''),('WESkit','c6151be7-666a-487a-ad06-615fe9997983',_binary '\0'),('WESkit','d4b72e00-8775-47e0-8412-8cac6a2c3054',_binary '\0'),('WESkit','d7825fa7-20e1-43af-9ced-2a9d44117616',_binary '\0');
/*!40000 ALTER TABLE `DEFAULT_CLIENT_SCOPE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `EVENT_ENTITY`
--

DROP TABLE IF EXISTS `EVENT_ENTITY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `EVENT_ENTITY` (
  `ID` varchar(36) NOT NULL,
  `CLIENT_ID` varchar(255) DEFAULT NULL,
  `DETAILS_JSON` text,
  `ERROR` varchar(255) DEFAULT NULL,
  `IP_ADDRESS` varchar(255) DEFAULT NULL,
  `REALM_ID` varchar(255) DEFAULT NULL,
  `SESSION_ID` varchar(255) DEFAULT NULL,
  `EVENT_TIME` bigint DEFAULT NULL,
  `TYPE` varchar(255) DEFAULT NULL,
  `USER_ID` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_EVENT_TIME` (`REALM_ID`,`EVENT_TIME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `EVENT_ENTITY`
--

LOCK TABLES `EVENT_ENTITY` WRITE;
/*!40000 ALTER TABLE `EVENT_ENTITY` DISABLE KEYS */;
/*!40000 ALTER TABLE `EVENT_ENTITY` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FEDERATED_IDENTITY`
--

DROP TABLE IF EXISTS `FEDERATED_IDENTITY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `FEDERATED_IDENTITY` (
  `IDENTITY_PROVIDER` varchar(255) NOT NULL,
  `REALM_ID` varchar(36) DEFAULT NULL,
  `FEDERATED_USER_ID` varchar(255) DEFAULT NULL,
  `FEDERATED_USERNAME` varchar(255) DEFAULT NULL,
  `TOKEN` text,
  `USER_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`IDENTITY_PROVIDER`,`USER_ID`),
  KEY `IDX_FEDIDENTITY_USER` (`USER_ID`),
  KEY `IDX_FEDIDENTITY_FEDUSER` (`FEDERATED_USER_ID`),
  CONSTRAINT `FK404288B92EF007A6` FOREIGN KEY (`USER_ID`) REFERENCES `USER_ENTITY` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FEDERATED_IDENTITY`
--

LOCK TABLES `FEDERATED_IDENTITY` WRITE;
/*!40000 ALTER TABLE `FEDERATED_IDENTITY` DISABLE KEYS */;
/*!40000 ALTER TABLE `FEDERATED_IDENTITY` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FEDERATED_USER`
--

DROP TABLE IF EXISTS `FEDERATED_USER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `FEDERATED_USER` (
  `ID` varchar(255) NOT NULL,
  `STORAGE_PROVIDER_ID` varchar(255) DEFAULT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FEDERATED_USER`
--

LOCK TABLES `FEDERATED_USER` WRITE;
/*!40000 ALTER TABLE `FEDERATED_USER` DISABLE KEYS */;
/*!40000 ALTER TABLE `FEDERATED_USER` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FED_USER_ATTRIBUTE`
--

DROP TABLE IF EXISTS `FED_USER_ATTRIBUTE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `FED_USER_ATTRIBUTE` (
  `ID` varchar(36) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `USER_ID` varchar(255) NOT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  `STORAGE_PROVIDER_ID` varchar(36) DEFAULT NULL,
  `VALUE` text,
  PRIMARY KEY (`ID`),
  KEY `IDX_FU_ATTRIBUTE` (`USER_ID`,`REALM_ID`,`NAME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FED_USER_ATTRIBUTE`
--

LOCK TABLES `FED_USER_ATTRIBUTE` WRITE;
/*!40000 ALTER TABLE `FED_USER_ATTRIBUTE` DISABLE KEYS */;
/*!40000 ALTER TABLE `FED_USER_ATTRIBUTE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FED_USER_CONSENT`
--

DROP TABLE IF EXISTS `FED_USER_CONSENT`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `FED_USER_CONSENT` (
  `ID` varchar(36) NOT NULL,
  `CLIENT_ID` varchar(255) DEFAULT NULL,
  `USER_ID` varchar(255) NOT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  `STORAGE_PROVIDER_ID` varchar(36) DEFAULT NULL,
  `CREATED_DATE` bigint DEFAULT NULL,
  `LAST_UPDATED_DATE` bigint DEFAULT NULL,
  `CLIENT_STORAGE_PROVIDER` varchar(36) DEFAULT NULL,
  `EXTERNAL_CLIENT_ID` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_FU_CONSENT` (`USER_ID`,`CLIENT_ID`),
  KEY `IDX_FU_CONSENT_RU` (`REALM_ID`,`USER_ID`),
  KEY `IDX_FU_CNSNT_EXT` (`USER_ID`,`CLIENT_STORAGE_PROVIDER`,`EXTERNAL_CLIENT_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FED_USER_CONSENT`
--

LOCK TABLES `FED_USER_CONSENT` WRITE;
/*!40000 ALTER TABLE `FED_USER_CONSENT` DISABLE KEYS */;
/*!40000 ALTER TABLE `FED_USER_CONSENT` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FED_USER_CONSENT_CL_SCOPE`
--

DROP TABLE IF EXISTS `FED_USER_CONSENT_CL_SCOPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `FED_USER_CONSENT_CL_SCOPE` (
  `USER_CONSENT_ID` varchar(36) NOT NULL,
  `SCOPE_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`USER_CONSENT_ID`,`SCOPE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FED_USER_CONSENT_CL_SCOPE`
--

LOCK TABLES `FED_USER_CONSENT_CL_SCOPE` WRITE;
/*!40000 ALTER TABLE `FED_USER_CONSENT_CL_SCOPE` DISABLE KEYS */;
/*!40000 ALTER TABLE `FED_USER_CONSENT_CL_SCOPE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FED_USER_CREDENTIAL`
--

DROP TABLE IF EXISTS `FED_USER_CREDENTIAL`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `FED_USER_CREDENTIAL` (
  `ID` varchar(36) NOT NULL,
  `SALT` tinyblob,
  `TYPE` varchar(255) DEFAULT NULL,
  `CREATED_DATE` bigint DEFAULT NULL,
  `USER_ID` varchar(255) NOT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  `STORAGE_PROVIDER_ID` varchar(36) DEFAULT NULL,
  `USER_LABEL` varchar(255) DEFAULT NULL,
  `SECRET_DATA` longtext,
  `CREDENTIAL_DATA` longtext,
  `PRIORITY` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_FU_CREDENTIAL` (`USER_ID`,`TYPE`),
  KEY `IDX_FU_CREDENTIAL_RU` (`REALM_ID`,`USER_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FED_USER_CREDENTIAL`
--

LOCK TABLES `FED_USER_CREDENTIAL` WRITE;
/*!40000 ALTER TABLE `FED_USER_CREDENTIAL` DISABLE KEYS */;
/*!40000 ALTER TABLE `FED_USER_CREDENTIAL` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FED_USER_GROUP_MEMBERSHIP`
--

DROP TABLE IF EXISTS `FED_USER_GROUP_MEMBERSHIP`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `FED_USER_GROUP_MEMBERSHIP` (
  `GROUP_ID` varchar(36) NOT NULL,
  `USER_ID` varchar(255) NOT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  `STORAGE_PROVIDER_ID` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`GROUP_ID`,`USER_ID`),
  KEY `IDX_FU_GROUP_MEMBERSHIP` (`USER_ID`,`GROUP_ID`),
  KEY `IDX_FU_GROUP_MEMBERSHIP_RU` (`REALM_ID`,`USER_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FED_USER_GROUP_MEMBERSHIP`
--

LOCK TABLES `FED_USER_GROUP_MEMBERSHIP` WRITE;
/*!40000 ALTER TABLE `FED_USER_GROUP_MEMBERSHIP` DISABLE KEYS */;
/*!40000 ALTER TABLE `FED_USER_GROUP_MEMBERSHIP` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FED_USER_REQUIRED_ACTION`
--

DROP TABLE IF EXISTS `FED_USER_REQUIRED_ACTION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `FED_USER_REQUIRED_ACTION` (
  `REQUIRED_ACTION` varchar(255) NOT NULL DEFAULT ' ',
  `USER_ID` varchar(255) NOT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  `STORAGE_PROVIDER_ID` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`REQUIRED_ACTION`,`USER_ID`),
  KEY `IDX_FU_REQUIRED_ACTION` (`USER_ID`,`REQUIRED_ACTION`),
  KEY `IDX_FU_REQUIRED_ACTION_RU` (`REALM_ID`,`USER_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FED_USER_REQUIRED_ACTION`
--

LOCK TABLES `FED_USER_REQUIRED_ACTION` WRITE;
/*!40000 ALTER TABLE `FED_USER_REQUIRED_ACTION` DISABLE KEYS */;
/*!40000 ALTER TABLE `FED_USER_REQUIRED_ACTION` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FED_USER_ROLE_MAPPING`
--

DROP TABLE IF EXISTS `FED_USER_ROLE_MAPPING`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `FED_USER_ROLE_MAPPING` (
  `ROLE_ID` varchar(36) NOT NULL,
  `USER_ID` varchar(255) NOT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  `STORAGE_PROVIDER_ID` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`ROLE_ID`,`USER_ID`),
  KEY `IDX_FU_ROLE_MAPPING` (`USER_ID`,`ROLE_ID`),
  KEY `IDX_FU_ROLE_MAPPING_RU` (`REALM_ID`,`USER_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FED_USER_ROLE_MAPPING`
--

LOCK TABLES `FED_USER_ROLE_MAPPING` WRITE;
/*!40000 ALTER TABLE `FED_USER_ROLE_MAPPING` DISABLE KEYS */;
/*!40000 ALTER TABLE `FED_USER_ROLE_MAPPING` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `GROUP_ATTRIBUTE`
--

DROP TABLE IF EXISTS `GROUP_ATTRIBUTE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `GROUP_ATTRIBUTE` (
  `ID` varchar(36) NOT NULL DEFAULT 'sybase-needs-something-here',
  `NAME` varchar(255) NOT NULL,
  `VALUE` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `GROUP_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_GROUP_ATTR_GROUP` (`GROUP_ID`),
  CONSTRAINT `FK_GROUP_ATTRIBUTE_GROUP` FOREIGN KEY (`GROUP_ID`) REFERENCES `KEYCLOAK_GROUP` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `GROUP_ATTRIBUTE`
--

LOCK TABLES `GROUP_ATTRIBUTE` WRITE;
/*!40000 ALTER TABLE `GROUP_ATTRIBUTE` DISABLE KEYS */;
/*!40000 ALTER TABLE `GROUP_ATTRIBUTE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `GROUP_ROLE_MAPPING`
--

DROP TABLE IF EXISTS `GROUP_ROLE_MAPPING`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `GROUP_ROLE_MAPPING` (
  `ROLE_ID` varchar(36) NOT NULL,
  `GROUP_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`ROLE_ID`,`GROUP_ID`),
  KEY `IDX_GROUP_ROLE_MAPP_GROUP` (`GROUP_ID`),
  CONSTRAINT `FK_GROUP_ROLE_GROUP` FOREIGN KEY (`GROUP_ID`) REFERENCES `KEYCLOAK_GROUP` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `GROUP_ROLE_MAPPING`
--

LOCK TABLES `GROUP_ROLE_MAPPING` WRITE;
/*!40000 ALTER TABLE `GROUP_ROLE_MAPPING` DISABLE KEYS */;
/*!40000 ALTER TABLE `GROUP_ROLE_MAPPING` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IDENTITY_PROVIDER`
--

DROP TABLE IF EXISTS `IDENTITY_PROVIDER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `IDENTITY_PROVIDER` (
  `INTERNAL_ID` varchar(36) NOT NULL,
  `ENABLED` bit(1) NOT NULL DEFAULT b'0',
  `PROVIDER_ALIAS` varchar(255) DEFAULT NULL,
  `PROVIDER_ID` varchar(255) DEFAULT NULL,
  `STORE_TOKEN` bit(1) NOT NULL DEFAULT b'0',
  `AUTHENTICATE_BY_DEFAULT` bit(1) NOT NULL DEFAULT b'0',
  `REALM_ID` varchar(36) DEFAULT NULL,
  `ADD_TOKEN_ROLE` bit(1) NOT NULL DEFAULT b'1',
  `TRUST_EMAIL` bit(1) NOT NULL DEFAULT b'0',
  `FIRST_BROKER_LOGIN_FLOW_ID` varchar(36) DEFAULT NULL,
  `POST_BROKER_LOGIN_FLOW_ID` varchar(36) DEFAULT NULL,
  `PROVIDER_DISPLAY_NAME` varchar(255) DEFAULT NULL,
  `LINK_ONLY` bit(1) NOT NULL DEFAULT b'0',
  PRIMARY KEY (`INTERNAL_ID`),
  UNIQUE KEY `UK_2DAELWNIBJI49AVXSRTUF6XJ33` (`PROVIDER_ALIAS`,`REALM_ID`),
  KEY `IDX_IDENT_PROV_REALM` (`REALM_ID`),
  CONSTRAINT `FK2B4EBC52AE5C3B34` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IDENTITY_PROVIDER`
--

LOCK TABLES `IDENTITY_PROVIDER` WRITE;
/*!40000 ALTER TABLE `IDENTITY_PROVIDER` DISABLE KEYS */;
/*!40000 ALTER TABLE `IDENTITY_PROVIDER` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IDENTITY_PROVIDER_CONFIG`
--

DROP TABLE IF EXISTS `IDENTITY_PROVIDER_CONFIG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `IDENTITY_PROVIDER_CONFIG` (
  `IDENTITY_PROVIDER_ID` varchar(36) NOT NULL,
  `VALUE` longtext,
  `NAME` varchar(255) NOT NULL,
  PRIMARY KEY (`IDENTITY_PROVIDER_ID`,`NAME`),
  CONSTRAINT `FKDC4897CF864C4E43` FOREIGN KEY (`IDENTITY_PROVIDER_ID`) REFERENCES `IDENTITY_PROVIDER` (`INTERNAL_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IDENTITY_PROVIDER_CONFIG`
--

LOCK TABLES `IDENTITY_PROVIDER_CONFIG` WRITE;
/*!40000 ALTER TABLE `IDENTITY_PROVIDER_CONFIG` DISABLE KEYS */;
/*!40000 ALTER TABLE `IDENTITY_PROVIDER_CONFIG` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IDENTITY_PROVIDER_MAPPER`
--

DROP TABLE IF EXISTS `IDENTITY_PROVIDER_MAPPER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `IDENTITY_PROVIDER_MAPPER` (
  `ID` varchar(36) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `IDP_ALIAS` varchar(255) NOT NULL,
  `IDP_MAPPER_NAME` varchar(255) NOT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_ID_PROV_MAPP_REALM` (`REALM_ID`),
  CONSTRAINT `FK_IDPM_REALM` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IDENTITY_PROVIDER_MAPPER`
--

LOCK TABLES `IDENTITY_PROVIDER_MAPPER` WRITE;
/*!40000 ALTER TABLE `IDENTITY_PROVIDER_MAPPER` DISABLE KEYS */;
/*!40000 ALTER TABLE `IDENTITY_PROVIDER_MAPPER` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IDP_MAPPER_CONFIG`
--

DROP TABLE IF EXISTS `IDP_MAPPER_CONFIG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `IDP_MAPPER_CONFIG` (
  `IDP_MAPPER_ID` varchar(36) NOT NULL,
  `VALUE` longtext,
  `NAME` varchar(255) NOT NULL,
  PRIMARY KEY (`IDP_MAPPER_ID`,`NAME`),
  CONSTRAINT `FK_IDPMCONFIG` FOREIGN KEY (`IDP_MAPPER_ID`) REFERENCES `IDENTITY_PROVIDER_MAPPER` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IDP_MAPPER_CONFIG`
--

LOCK TABLES `IDP_MAPPER_CONFIG` WRITE;
/*!40000 ALTER TABLE `IDP_MAPPER_CONFIG` DISABLE KEYS */;
/*!40000 ALTER TABLE `IDP_MAPPER_CONFIG` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `KEYCLOAK_GROUP`
--

DROP TABLE IF EXISTS `KEYCLOAK_GROUP`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `KEYCLOAK_GROUP` (
  `ID` varchar(36) NOT NULL,
  `NAME` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `PARENT_GROUP` varchar(36) NOT NULL,
  `REALM_ID` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `SIBLING_NAMES` (`REALM_ID`,`PARENT_GROUP`,`NAME`),
  CONSTRAINT `FK_GROUP_REALM` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `KEYCLOAK_GROUP`
--

LOCK TABLES `KEYCLOAK_GROUP` WRITE;
/*!40000 ALTER TABLE `KEYCLOAK_GROUP` DISABLE KEYS */;
INSERT INTO `KEYCLOAK_GROUP` VALUES ('f81b7661-401b-49f7-93c0-794f6683673b','fooo',' ','WESkit');
/*!40000 ALTER TABLE `KEYCLOAK_GROUP` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `KEYCLOAK_ROLE`
--

DROP TABLE IF EXISTS `KEYCLOAK_ROLE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `KEYCLOAK_ROLE` (
  `ID` varchar(36) NOT NULL,
  `CLIENT_REALM_CONSTRAINT` varchar(255) DEFAULT NULL,
  `CLIENT_ROLE` bit(1) DEFAULT NULL,
  `DESCRIPTION` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `NAME` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `REALM_ID` varchar(255) DEFAULT NULL,
  `CLIENT` varchar(36) DEFAULT NULL,
  `REALM` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `UK_J3RWUVD56ONTGSUHOGM184WW2-2` (`NAME`,`CLIENT_REALM_CONSTRAINT`),
  KEY `IDX_KEYCLOAK_ROLE_CLIENT` (`CLIENT`),
  KEY `IDX_KEYCLOAK_ROLE_REALM` (`REALM`),
  CONSTRAINT `FK_6VYQFE4CN4WLQ8R6KT5VDSJ5C` FOREIGN KEY (`REALM`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `KEYCLOAK_ROLE`
--

LOCK TABLES `KEYCLOAK_ROLE` WRITE;
/*!40000 ALTER TABLE `KEYCLOAK_ROLE` DISABLE KEYS */;
INSERT INTO `KEYCLOAK_ROLE` VALUES ('02a5d5df-98a6-4b2d-8bbe-bde39eec7995','master',_binary '\0','${role_uma_authorization}','uma_authorization','master',NULL,'master'),('06f41222-5675-4a54-b953-421944c02923','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_query-realms}','query-realms','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('1328a8ef-2469-4c83-afba-8d96f2e93a28','master',_binary '\0','${role_create-realm}','create-realm','master',NULL,'master'),('1aab2464-0a06-4a68-bb9d-9a625c2e156e','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_view-realm}','view-realm','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('1f25214f-98b1-4fb6-8ccf-c1480cbb8d35','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_manage-realm}','manage-realm','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('248a3f39-6dfe-422f-8c29-70c6669842fc','e47088a1-3190-435b-a237-e4e0b50988d5',_binary '','${role_manage-account}','manage-account','master','e47088a1-3190-435b-a237-e4e0b50988d5',NULL),('27483a2d-95b9-4636-b920-de432ef02565','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_create-client}','create-client','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('2df93e5a-7e08-459e-a1c0-4ecfc6ae00e4','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_query-users}','query-users','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('2e60536d-4ee4-47cf-8d19-4f5c844777f6','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_create-client}','create-client','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('2f449425-83d6-45a4-8814-04ed95b38fc0','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_view-clients}','view-clients','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('35518ac8-8630-4b11-8005-e2ce0dd3a39c','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_view-identity-providers}','view-identity-providers','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('39c4c0b3-ab8b-4479-be78-273b73992aa5','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_query-clients}','query-clients','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('3b6d5695-9dd8-44cd-bba7-8db9f71b6f2f','e47088a1-3190-435b-a237-e4e0b50988d5',_binary '','${role_view-consent}','view-consent','master','e47088a1-3190-435b-a237-e4e0b50988d5',NULL),('3b7b8cde-8644-4767-b8a2-efcaf0b809f3','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_view-events}','view-events','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('4408e590-d9bb-411b-86d5-56e9e6417409','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_impersonation}','impersonation','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('448fbe8c-3ffb-4dce-888c-a39dd187c4a5','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_query-users}','query-users','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('46cc8442-0314-4294-93eb-463e6a821bba','e47088a1-3190-435b-a237-e4e0b50988d5',_binary '','${role_manage-consent}','manage-consent','master','e47088a1-3190-435b-a237-e4e0b50988d5',NULL),('47457aeb-a463-489e-b7d7-fcfd0e21363a','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_view-authorization}','view-authorization','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('4d51c469-5b72-41ad-b987-b414839904aa','WESkit',_binary '\0','${role_uma_authorization}','uma_authorization','WESkit',NULL,'WESkit'),('4e7561b4-c79f-4d09-ba7f-a04b19a8b6cf','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_view-clients}','view-clients','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('4efe6faa-afd2-4690-98e2-4b2579adc59e','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_manage-events}','manage-events','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('51f32f82-e980-4711-8655-6735c76ac53e','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_query-groups}','query-groups','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('526de35b-4b08-492e-9f53-2a15aaf836b3','WESkit',_binary '\0',NULL,'WESkit_Admin','WESkit',NULL,'WESkit'),('52a3415d-65a9-4314-8805-c85ca05b55d6','WESkit',_binary '\0','${role_offline-access}','offline_access','WESkit',NULL,'WESkit'),('5596cc11-3a03-4c38-9e95-1cbea129bc81','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_realm-admin}','realm-admin','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('572afd3d-87ca-4e56-8adf-7e3b0fe01d93','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_query-groups}','query-groups','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('57420870-c874-4c4f-896f-bc17dc807fb1','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_manage-events}','manage-events','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('67358233-cc50-4565-b094-bab9d8a5ccd1','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_manage-clients}','manage-clients','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('6aeb41c8-8cd5-4bc7-b1ff-680579fdd828','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_impersonation}','impersonation','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('6b3dccf1-7b9c-40b3-988a-10b2179928de','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_manage-authorization}','manage-authorization','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('6c15817c-1196-487a-be12-c976b2d1b0cf','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_manage-clients}','manage-clients','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('6cc9a54c-c82b-403f-bf4f-49679e6b8e53','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_manage-authorization}','manage-authorization','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('6d540935-0f0f-4e77-b138-62338d49be17','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_query-realms}','query-realms','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('6d9ce5c4-e378-416b-ac64-257a69617f82','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_view-authorization}','view-authorization','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('73cedc68-b7bf-40ad-82a7-50f4baab3d17','48ca4365-c4d8-477b-91ce-d3509dc77334',_binary '',NULL,'WESkit_Admin2','WESkit','48ca4365-c4d8-477b-91ce-d3509dc77334',NULL),('7972d87f-9237-48c3-94c9-cdc64d1305c8','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_create-client}','create-client','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('7a7d7dc3-3c1a-4ed1-888a-935478758892','77249ec3-5596-4d8b-a2d3-15604ca70de5',_binary '','${role_manage-account-links}','manage-account-links','WESkit','77249ec3-5596-4d8b-a2d3-15604ca70de5',NULL),('7b3f7c39-8476-44b8-8bab-9f2fa2ed6295','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_manage-users}','manage-users','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('7fb99f4a-94c8-4888-987a-77b7dc255a30','e47088a1-3190-435b-a237-e4e0b50988d5',_binary '','${role_manage-account-links}','manage-account-links','master','e47088a1-3190-435b-a237-e4e0b50988d5',NULL),('88a8bbe2-97f2-49d6-af00-60b540d73fcf','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_view-realm}','view-realm','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('8932ca33-75ab-4a41-b915-d0e368a30c5c','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_manage-events}','manage-events','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('9072651e-bcb8-4b9c-96de-057ed5ea9cdb','e47088a1-3190-435b-a237-e4e0b50988d5',_binary '','${role_view-applications}','view-applications','master','e47088a1-3190-435b-a237-e4e0b50988d5',NULL),('9a31d20b-e9aa-4983-8465-b94ee9fb3b79','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_query-groups}','query-groups','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('9c8169aa-b379-409b-bbe3-42592be27747','master',_binary '\0','${role_admin}','admin','master',NULL,'master'),('9e1c7db9-8233-4c8f-bc6e-b3820d98d642','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_view-clients}','view-clients','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('9fe0f5ad-7ef3-4cd5-b216-9fc0e4021bf4','77249ec3-5596-4d8b-a2d3-15604ca70de5',_binary '','${role_manage-account}','manage-account','WESkit','77249ec3-5596-4d8b-a2d3-15604ca70de5',NULL),('a1583b65-4e81-495c-a968-c163fe412d1c','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_query-users}','query-users','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('b0025059-e023-4fde-836c-a0e12b9941b6','e47088a1-3190-435b-a237-e4e0b50988d5',_binary '','${role_view-profile}','view-profile','master','e47088a1-3190-435b-a237-e4e0b50988d5',NULL),('b0bf3bf5-ad75-4eca-939a-fcfcab9ab018','77249ec3-5596-4d8b-a2d3-15604ca70de5',_binary '','${role_view-consent}','view-consent','WESkit','77249ec3-5596-4d8b-a2d3-15604ca70de5',NULL),('b48f8fd3-34b9-4321-ae27-5a071e889238','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_view-identity-providers}','view-identity-providers','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('b5570588-5cba-455a-97a7-2f2c8939a044','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_view-events}','view-events','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('b6e22a8b-860f-4805-a291-d8ae6d3c1878','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_manage-realm}','manage-realm','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('bb90e6ad-005d-4711-a399-55c4730dca1a','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_manage-identity-providers}','manage-identity-providers','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('bebfe83d-f732-4aa6-a3f8-421d3f2ec346','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_view-users}','view-users','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('c3424f59-cc83-4d26-9839-86552a1cd03b','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_query-clients}','query-clients','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('c3c522fb-be42-49d7-924d-72df2fa9b7ae','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_manage-clients}','manage-clients','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('c40b393e-e3eb-4e08-b764-d05f692b3817','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_query-realms}','query-realms','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('c8d9813c-3240-404a-a976-92917ff894a7','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_view-identity-providers}','view-identity-providers','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('c9143bcc-c2ab-45e9-9434-496669091ac5','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_manage-identity-providers}','manage-identity-providers','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('ca651a58-d1e1-436f-8aa0-295e305c9df2','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_view-authorization}','view-authorization','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('cbc5dbe2-ac59-4b57-a641-387d94e759c6','master',_binary '\0','${role_offline-access}','offline_access','master',NULL,'master'),('cf164202-e2b5-44fd-808e-69c3294087a4','77249ec3-5596-4d8b-a2d3-15604ca70de5',_binary '','${role_delete-account}','delete-account','WESkit','77249ec3-5596-4d8b-a2d3-15604ca70de5',NULL),('d09037a6-8d92-48d0-968b-e05fb0cb7282','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_query-clients}','query-clients','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('d6eee359-4ca1-4363-9b52-a5ea49812527','e47088a1-3190-435b-a237-e4e0b50988d5',_binary '','${role_delete-account}','delete-account','master','e47088a1-3190-435b-a237-e4e0b50988d5',NULL),('d7c862d5-179c-4fd5-a116-6e8bf84fd94c','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_view-users}','view-users','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('dc443104-cd3f-4914-9fa6-5bfc52bbd1a0','8ae1bc8c-be2e-4b41-943c-63bd2aaf0e03',_binary '','${role_read-token}','read-token','master','8ae1bc8c-be2e-4b41-943c-63bd2aaf0e03',NULL),('dc60a653-a1c6-44cb-abe8-e8db215ef0f8','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_manage-realm}','manage-realm','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('dfa5c730-cf74-4eaa-93c6-f3566f177edc','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_view-users}','view-users','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('dff6c1e5-d410-4680-a6d4-d420fa3dc329','69131d51-8b86-4470-a07c-a51305df8782',_binary '','${role_impersonation}','impersonation','master','69131d51-8b86-4470-a07c-a51305df8782',NULL),('e3c3bc13-bb35-46a7-a295-d35acf568419','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_manage-users}','manage-users','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('e929cb6b-7f9b-484f-a13e-03d2925a6f2c','77249ec3-5596-4d8b-a2d3-15604ca70de5',_binary '','${role_view-applications}','view-applications','WESkit','77249ec3-5596-4d8b-a2d3-15604ca70de5',NULL),('e963003d-a6f9-40e1-a14d-df4af02da9be','77249ec3-5596-4d8b-a2d3-15604ca70de5',_binary '','${role_view-profile}','view-profile','WESkit','77249ec3-5596-4d8b-a2d3-15604ca70de5',NULL),('eccd5ee8-068c-4a06-aed4-b5098bb78f50','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_manage-authorization}','manage-authorization','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('ecef566e-72b5-477c-a1ef-5d4adb540cc4','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_view-realm}','view-realm','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('f31579ab-a1b5-444f-9678-d1496dec385b','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_view-events}','view-events','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('f909efa7-c95d-4afd-ba47-3c8d4d4dd960','3e40f193-9407-4729-88c2-95fcc3ab220f',_binary '','${role_manage-identity-providers}','manage-identity-providers','master','3e40f193-9407-4729-88c2-95fcc3ab220f',NULL),('f96d9c1d-253f-4e51-86fb-844b2cdc84f4','77249ec3-5596-4d8b-a2d3-15604ca70de5',_binary '','${role_manage-consent}','manage-consent','WESkit','77249ec3-5596-4d8b-a2d3-15604ca70de5',NULL),('fbde0c90-661c-4c6a-bd4c-67414d97536a','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',_binary '','${role_manage-users}','manage-users','WESkit','25c61f98-bb03-41f6-b5d1-53e0884aa1c4',NULL),('fec6bc1a-bb38-4c40-be99-f578eceab8f9','2ba5388c-d47c-4d80-b9bd-3d9bab15f3be',_binary '','${role_read-token}','read-token','WESkit','2ba5388c-d47c-4d80-b9bd-3d9bab15f3be',NULL);
/*!40000 ALTER TABLE `KEYCLOAK_ROLE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MIGRATION_MODEL`
--

DROP TABLE IF EXISTS `MIGRATION_MODEL`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MIGRATION_MODEL` (
  `ID` varchar(36) NOT NULL,
  `VERSION` varchar(36) DEFAULT NULL,
  `UPDATE_TIME` bigint NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`),
  KEY `IDX_UPDATE_TIME` (`UPDATE_TIME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MIGRATION_MODEL`
--

LOCK TABLES `MIGRATION_MODEL` WRITE;
/*!40000 ALTER TABLE `MIGRATION_MODEL` DISABLE KEYS */;
INSERT INTO `MIGRATION_MODEL` VALUES ('l5q2l','12.0.2',1614172208);
/*!40000 ALTER TABLE `MIGRATION_MODEL` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `OFFLINE_CLIENT_SESSION`
--

DROP TABLE IF EXISTS `OFFLINE_CLIENT_SESSION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `OFFLINE_CLIENT_SESSION` (
  `USER_SESSION_ID` varchar(36) NOT NULL,
  `CLIENT_ID` varchar(255) NOT NULL,
  `OFFLINE_FLAG` varchar(4) NOT NULL,
  `TIMESTAMP` int DEFAULT NULL,
  `DATA` longtext,
  `CLIENT_STORAGE_PROVIDER` varchar(36) NOT NULL DEFAULT 'local',
  `EXTERNAL_CLIENT_ID` varchar(255) NOT NULL DEFAULT 'local',
  PRIMARY KEY (`USER_SESSION_ID`,`CLIENT_ID`,`CLIENT_STORAGE_PROVIDER`,`EXTERNAL_CLIENT_ID`,`OFFLINE_FLAG`),
  KEY `IDX_US_SESS_ID_ON_CL_SESS` (`USER_SESSION_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `OFFLINE_CLIENT_SESSION`
--

LOCK TABLES `OFFLINE_CLIENT_SESSION` WRITE;
/*!40000 ALTER TABLE `OFFLINE_CLIENT_SESSION` DISABLE KEYS */;
/*!40000 ALTER TABLE `OFFLINE_CLIENT_SESSION` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `OFFLINE_USER_SESSION`
--

DROP TABLE IF EXISTS `OFFLINE_USER_SESSION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `OFFLINE_USER_SESSION` (
  `USER_SESSION_ID` varchar(36) NOT NULL,
  `USER_ID` varchar(255) DEFAULT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  `CREATED_ON` int NOT NULL,
  `OFFLINE_FLAG` varchar(4) NOT NULL,
  `DATA` longtext,
  `LAST_SESSION_REFRESH` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`USER_SESSION_ID`,`OFFLINE_FLAG`),
  KEY `IDX_OFFLINE_USS_CREATEDON` (`CREATED_ON`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `OFFLINE_USER_SESSION`
--

LOCK TABLES `OFFLINE_USER_SESSION` WRITE;
/*!40000 ALTER TABLE `OFFLINE_USER_SESSION` DISABLE KEYS */;
/*!40000 ALTER TABLE `OFFLINE_USER_SESSION` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `POLICY_CONFIG`
--

DROP TABLE IF EXISTS `POLICY_CONFIG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `POLICY_CONFIG` (
  `POLICY_ID` varchar(36) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `VALUE` longtext,
  PRIMARY KEY (`POLICY_ID`,`NAME`),
  CONSTRAINT `FKDC34197CF864C4E43` FOREIGN KEY (`POLICY_ID`) REFERENCES `RESOURCE_SERVER_POLICY` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `POLICY_CONFIG`
--

LOCK TABLES `POLICY_CONFIG` WRITE;
/*!40000 ALTER TABLE `POLICY_CONFIG` DISABLE KEYS */;
/*!40000 ALTER TABLE `POLICY_CONFIG` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PROTOCOL_MAPPER`
--

DROP TABLE IF EXISTS `PROTOCOL_MAPPER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PROTOCOL_MAPPER` (
  `ID` varchar(36) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `PROTOCOL` varchar(255) NOT NULL,
  `PROTOCOL_MAPPER_NAME` varchar(255) NOT NULL,
  `CLIENT_ID` varchar(36) DEFAULT NULL,
  `CLIENT_SCOPE_ID` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_PROTOCOL_MAPPER_CLIENT` (`CLIENT_ID`),
  KEY `IDX_CLSCOPE_PROTMAP` (`CLIENT_SCOPE_ID`),
  CONSTRAINT `FK_CLI_SCOPE_MAPPER` FOREIGN KEY (`CLIENT_SCOPE_ID`) REFERENCES `CLIENT_SCOPE` (`ID`),
  CONSTRAINT `FK_PCM_REALM` FOREIGN KEY (`CLIENT_ID`) REFERENCES `CLIENT` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PROTOCOL_MAPPER`
--

LOCK TABLES `PROTOCOL_MAPPER` WRITE;
/*!40000 ALTER TABLE `PROTOCOL_MAPPER` DISABLE KEYS */;
INSERT INTO `PROTOCOL_MAPPER` VALUES ('098f13db-1bc0-427a-9cc1-d4f42bb530fa','audience resolve','openid-connect','oidc-audience-resolve-mapper',NULL,'1f6b4061-797c-4caf-b130-c7ced3da55a7'),('12222055-1409-40c2-80c0-bae6b2224fc0','locale','openid-connect','oidc-usermodel-attribute-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('1660ddd0-29f3-4a62-aefb-f86c92bf3751','address','openid-connect','oidc-address-mapper',NULL,'d4b72e00-8775-47e0-8412-8cac6a2c3054'),('1a5039b0-4181-4dfd-885b-2f0045d6dd57','locale','openid-connect','oidc-usermodel-attribute-mapper','4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a',NULL),('1b44e30b-f01b-414a-8535-9c7c53d9cf60','locale','openid-connect','oidc-usermodel-attribute-mapper','6445f320-dddf-4a4f-8e54-4ec19fbcb7ae',NULL),('1d83d931-e937-4fee-b110-4f955056c60e','phone number verified','openid-connect','oidc-usermodel-attribute-mapper',NULL,'a968f0db-2113-4e70-960f-3c2e1c1d3e94'),('2125b043-af2e-45ec-870a-a5da0272cbd1','middle name','openid-connect','oidc-usermodel-attribute-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('223e6740-5e7a-402c-b0bc-91578261afac','client roles','openid-connect','oidc-usermodel-client-role-mapper',NULL,'1f6b4061-797c-4caf-b130-c7ced3da55a7'),('290a2cf3-5990-4724-a573-087c7b31bb3e','audience resolve','openid-connect','oidc-audience-resolve-mapper','e9783fd8-bd55-44f6-bbea-0325f9ca5e03',NULL),('2a84ad91-a4c9-4665-af62-cedaab52b8a1','username','openid-connect','oidc-usermodel-property-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('2d3e2dac-b7c1-416e-b5b7-a2a09b861424','zoneinfo','openid-connect','oidc-usermodel-attribute-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('3f8e8dba-dc16-463d-b184-4a547801a951','realm roles','openid-connect','oidc-usermodel-realm-role-mapper',NULL,'5bbfcb16-0bcb-49e6-a25c-a2ac6c795864'),('47459e44-afa0-4382-8c89-45155e55f680','family name','openid-connect','oidc-usermodel-property-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('4a4bf29e-6de8-4141-b4a5-77cf62e15252','email','openid-connect','oidc-usermodel-property-mapper',NULL,'daf2f7b7-f1c7-458f-8a62-d72cc891a82d'),('4cfb38ee-c76b-4e71-a893-88c824de7487','given name','openid-connect','oidc-usermodel-property-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('4f56c276-2518-4aaf-b449-d0e9baac3dba','phone number verified','openid-connect','oidc-usermodel-attribute-mapper',NULL,'4b170f2c-e31b-4d03-8a2a-b514b444bfa6'),('5441a18b-1473-4a26-a648-3f6c3ee5cb40','profile','openid-connect','oidc-usermodel-attribute-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('5aff14a7-012e-4097-ac43-101a8d6aaf04','website','openid-connect','oidc-usermodel-attribute-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('60b682a7-b238-4dbf-b4a2-10cfcbf78e53','realm roles','openid-connect','oidc-usermodel-realm-role-mapper',NULL,'1f6b4061-797c-4caf-b130-c7ced3da55a7'),('625803a4-22a6-4c44-9338-d865698221a6','upn','openid-connect','oidc-usermodel-property-mapper',NULL,'9730d937-6ad4-4e39-a78c-176e16c88b8f'),('65fda6df-3700-4cd6-aa9b-29ace9fa3c49','gender','openid-connect','oidc-usermodel-attribute-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('66cc58ba-99d9-49ad-b7db-4e948f634062','gender','openid-connect','oidc-usermodel-attribute-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('66ccd308-f1bd-454a-b64b-1ab02c66f1ca','updated at','openid-connect','oidc-usermodel-attribute-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('696a03c2-1a2b-41d7-b8af-7c70f09408f5','role list','saml','saml-role-list-mapper',NULL,'1fdf2898-fa16-457d-8d1b-89e86e0bef77'),('6a15a937-f212-465a-ae66-5e87c636bb56','phone number','openid-connect','oidc-usermodel-attribute-mapper',NULL,'a968f0db-2113-4e70-960f-3c2e1c1d3e94'),('6b8a0e43-8da6-4c7f-95e8-61f130b2a4b9','allowed web origins','openid-connect','oidc-allowed-origins-mapper',NULL,'bd2d9561-e102-45f0-a7c5-8fa07a8f925b'),('71e8357f-476f-46ef-ad82-33c5d8524951','picture','openid-connect','oidc-usermodel-attribute-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('785fba6a-28e2-419e-aaf2-245ac1722bc1','full name','openid-connect','oidc-full-name-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('7c01eb41-4481-40d7-ab7a-20633d511917','address','openid-connect','oidc-address-mapper',NULL,'d2557dc6-b207-4785-9db3-e88e0eca290c'),('80ee0847-5da0-4dbc-b443-97c4b84ff75f','birthdate','openid-connect','oidc-usermodel-attribute-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('8161e1c4-56d4-49c1-94be-d60f6dad1edd','middle name','openid-connect','oidc-usermodel-attribute-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('85b1dd59-436f-4696-8aed-429a9cdb0d7a','username','openid-connect','oidc-usermodel-property-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('87a2017c-4027-4d35-904c-3907fac2d342','groups','openid-connect','oidc-usermodel-realm-role-mapper',NULL,'d7825fa7-20e1-43af-9ced-2a9d44117616'),('9e15a34f-3e2d-4c81-bb5b-f7a535cdbe97','nickname','openid-connect','oidc-usermodel-attribute-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('a57b4d3d-ca1d-4beb-84ce-6adb8a7621d1','profile','openid-connect','oidc-usermodel-attribute-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('a6aa1859-410f-4b14-bc70-350689a2504e','birthdate','openid-connect','oidc-usermodel-attribute-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('a77d5d2b-ce76-415d-9d27-83ab92867b00','audience resolve','openid-connect','oidc-audience-resolve-mapper','5060e61b-233b-4347-94e2-4d84d3e67dcc',NULL),('a9603ebc-8d23-45ff-b073-5b57d5159c8e','nickname','openid-connect','oidc-usermodel-attribute-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('ab4f6ce2-fd08-43c9-8a16-c383d415a40e','given name','openid-connect','oidc-usermodel-property-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('adfa6519-6bfb-4804-9b9b-67809d4159f2','role list','saml','saml-role-list-mapper',NULL,'bf7d7aac-cafc-4db7-8702-e4ab8d79d7fb'),('ae27457a-a1e7-44ce-9b20-267ed969770d','groups','openid-connect','oidc-usermodel-realm-role-mapper',NULL,'9730d937-6ad4-4e39-a78c-176e16c88b8f'),('b35762ca-7c17-4708-8d21-5bc5c9945c98','client roles','openid-connect','oidc-usermodel-client-role-mapper',NULL,'5bbfcb16-0bcb-49e6-a25c-a2ac6c795864'),('b459c737-3dc3-46fa-9cc6-f027949754c0','phone number','openid-connect','oidc-usermodel-attribute-mapper',NULL,'4b170f2c-e31b-4d03-8a2a-b514b444bfa6'),('b5f331d7-d567-4eaa-990a-3ffdf5d931cb','updated at','openid-connect','oidc-usermodel-attribute-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('b705542e-7227-4e59-9a39-977b3351172e','email verified','openid-connect','oidc-usermodel-property-mapper',NULL,'daf2f7b7-f1c7-458f-8a62-d72cc891a82d'),('be44dbbf-dabe-493e-9032-29d5f6ec1ff9','picture','openid-connect','oidc-usermodel-attribute-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('c298514c-077d-4309-9335-788c64a9cab7','allowed web origins','openid-connect','oidc-allowed-origins-mapper',NULL,'69e1f2f9-5014-47df-b6aa-91ca814888df'),('c40a0475-73ee-479d-bb04-68d9e1b582cf','upn','openid-connect','oidc-usermodel-property-mapper',NULL,'d7825fa7-20e1-43af-9ced-2a9d44117616'),('c82c30d6-ab74-4555-83e2-f41fe726ac3a','email','openid-connect','oidc-usermodel-property-mapper',NULL,'1d548a75-32d2-458d-96e5-772421f7c1bd'),('d697a281-b936-459f-a05c-5d24a99ceb19','email verified','openid-connect','oidc-usermodel-property-mapper',NULL,'1d548a75-32d2-458d-96e5-772421f7c1bd'),('db2e520b-a53e-47cf-96d2-07cb714aacba','full name','openid-connect','oidc-full-name-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('dee3763a-9983-412d-b846-e87eed41f2db','locale','openid-connect','oidc-usermodel-attribute-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('e7777acf-d9f9-4968-9b37-f0924b4628d7','website','openid-connect','oidc-usermodel-attribute-mapper',NULL,'61cab59a-456f-4bc2-b11c-4398c498dd12'),('f9ee21de-2454-4a47-87eb-3ae3f6beaf73','audience resolve','openid-connect','oidc-audience-resolve-mapper',NULL,'5bbfcb16-0bcb-49e6-a25c-a2ac6c795864'),('fb9e50f2-80b6-497b-8255-f0740a126db4','zoneinfo','openid-connect','oidc-usermodel-attribute-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167'),('fdb8d711-44bf-4332-9273-31c4c19cd6bd','family name','openid-connect','oidc-usermodel-property-mapper',NULL,'21ac849d-f14e-4ecf-9e98-dc065603e167');
/*!40000 ALTER TABLE `PROTOCOL_MAPPER` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PROTOCOL_MAPPER_CONFIG`
--

DROP TABLE IF EXISTS `PROTOCOL_MAPPER_CONFIG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PROTOCOL_MAPPER_CONFIG` (
  `PROTOCOL_MAPPER_ID` varchar(36) NOT NULL,
  `VALUE` longtext,
  `NAME` varchar(255) NOT NULL,
  PRIMARY KEY (`PROTOCOL_MAPPER_ID`,`NAME`),
  CONSTRAINT `FK_PMCONFIG` FOREIGN KEY (`PROTOCOL_MAPPER_ID`) REFERENCES `PROTOCOL_MAPPER` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PROTOCOL_MAPPER_CONFIG`
--

LOCK TABLES `PROTOCOL_MAPPER_CONFIG` WRITE;
/*!40000 ALTER TABLE `PROTOCOL_MAPPER_CONFIG` DISABLE KEYS */;
INSERT INTO `PROTOCOL_MAPPER_CONFIG` VALUES ('12222055-1409-40c2-80c0-bae6b2224fc0','true','access.token.claim'),('12222055-1409-40c2-80c0-bae6b2224fc0','locale','claim.name'),('12222055-1409-40c2-80c0-bae6b2224fc0','true','id.token.claim'),('12222055-1409-40c2-80c0-bae6b2224fc0','String','jsonType.label'),('12222055-1409-40c2-80c0-bae6b2224fc0','locale','user.attribute'),('12222055-1409-40c2-80c0-bae6b2224fc0','true','userinfo.token.claim'),('1660ddd0-29f3-4a62-aefb-f86c92bf3751','true','access.token.claim'),('1660ddd0-29f3-4a62-aefb-f86c92bf3751','true','id.token.claim'),('1660ddd0-29f3-4a62-aefb-f86c92bf3751','country','user.attribute.country'),('1660ddd0-29f3-4a62-aefb-f86c92bf3751','formatted','user.attribute.formatted'),('1660ddd0-29f3-4a62-aefb-f86c92bf3751','locality','user.attribute.locality'),('1660ddd0-29f3-4a62-aefb-f86c92bf3751','postal_code','user.attribute.postal_code'),('1660ddd0-29f3-4a62-aefb-f86c92bf3751','region','user.attribute.region'),('1660ddd0-29f3-4a62-aefb-f86c92bf3751','street','user.attribute.street'),('1660ddd0-29f3-4a62-aefb-f86c92bf3751','true','userinfo.token.claim'),('1a5039b0-4181-4dfd-885b-2f0045d6dd57','true','access.token.claim'),('1a5039b0-4181-4dfd-885b-2f0045d6dd57','locale','claim.name'),('1a5039b0-4181-4dfd-885b-2f0045d6dd57','true','id.token.claim'),('1a5039b0-4181-4dfd-885b-2f0045d6dd57','String','jsonType.label'),('1a5039b0-4181-4dfd-885b-2f0045d6dd57','locale','user.attribute'),('1a5039b0-4181-4dfd-885b-2f0045d6dd57','true','userinfo.token.claim'),('1b44e30b-f01b-414a-8535-9c7c53d9cf60','true','access.token.claim'),('1b44e30b-f01b-414a-8535-9c7c53d9cf60','locale','claim.name'),('1b44e30b-f01b-414a-8535-9c7c53d9cf60','true','id.token.claim'),('1b44e30b-f01b-414a-8535-9c7c53d9cf60','String','jsonType.label'),('1b44e30b-f01b-414a-8535-9c7c53d9cf60','locale','user.attribute'),('1b44e30b-f01b-414a-8535-9c7c53d9cf60','true','userinfo.token.claim'),('1d83d931-e937-4fee-b110-4f955056c60e','true','access.token.claim'),('1d83d931-e937-4fee-b110-4f955056c60e','phone_number_verified','claim.name'),('1d83d931-e937-4fee-b110-4f955056c60e','true','id.token.claim'),('1d83d931-e937-4fee-b110-4f955056c60e','boolean','jsonType.label'),('1d83d931-e937-4fee-b110-4f955056c60e','phoneNumberVerified','user.attribute'),('1d83d931-e937-4fee-b110-4f955056c60e','true','userinfo.token.claim'),('2125b043-af2e-45ec-870a-a5da0272cbd1','true','access.token.claim'),('2125b043-af2e-45ec-870a-a5da0272cbd1','middle_name','claim.name'),('2125b043-af2e-45ec-870a-a5da0272cbd1','true','id.token.claim'),('2125b043-af2e-45ec-870a-a5da0272cbd1','String','jsonType.label'),('2125b043-af2e-45ec-870a-a5da0272cbd1','middleName','user.attribute'),('2125b043-af2e-45ec-870a-a5da0272cbd1','true','userinfo.token.claim'),('223e6740-5e7a-402c-b0bc-91578261afac','true','access.token.claim'),('223e6740-5e7a-402c-b0bc-91578261afac','resource_access.${client_id}.roles','claim.name'),('223e6740-5e7a-402c-b0bc-91578261afac','String','jsonType.label'),('223e6740-5e7a-402c-b0bc-91578261afac','true','multivalued'),('223e6740-5e7a-402c-b0bc-91578261afac','foo','user.attribute'),('2a84ad91-a4c9-4665-af62-cedaab52b8a1','true','access.token.claim'),('2a84ad91-a4c9-4665-af62-cedaab52b8a1','preferred_username','claim.name'),('2a84ad91-a4c9-4665-af62-cedaab52b8a1','true','id.token.claim'),('2a84ad91-a4c9-4665-af62-cedaab52b8a1','String','jsonType.label'),('2a84ad91-a4c9-4665-af62-cedaab52b8a1','username','user.attribute'),('2a84ad91-a4c9-4665-af62-cedaab52b8a1','true','userinfo.token.claim'),('2d3e2dac-b7c1-416e-b5b7-a2a09b861424','true','access.token.claim'),('2d3e2dac-b7c1-416e-b5b7-a2a09b861424','zoneinfo','claim.name'),('2d3e2dac-b7c1-416e-b5b7-a2a09b861424','true','id.token.claim'),('2d3e2dac-b7c1-416e-b5b7-a2a09b861424','String','jsonType.label'),('2d3e2dac-b7c1-416e-b5b7-a2a09b861424','zoneinfo','user.attribute'),('2d3e2dac-b7c1-416e-b5b7-a2a09b861424','true','userinfo.token.claim'),('3f8e8dba-dc16-463d-b184-4a547801a951','true','access.token.claim'),('3f8e8dba-dc16-463d-b184-4a547801a951','realm_access.roles','claim.name'),('3f8e8dba-dc16-463d-b184-4a547801a951','String','jsonType.label'),('3f8e8dba-dc16-463d-b184-4a547801a951','true','multivalued'),('3f8e8dba-dc16-463d-b184-4a547801a951','foo','user.attribute'),('47459e44-afa0-4382-8c89-45155e55f680','true','access.token.claim'),('47459e44-afa0-4382-8c89-45155e55f680','family_name','claim.name'),('47459e44-afa0-4382-8c89-45155e55f680','true','id.token.claim'),('47459e44-afa0-4382-8c89-45155e55f680','String','jsonType.label'),('47459e44-afa0-4382-8c89-45155e55f680','lastName','user.attribute'),('47459e44-afa0-4382-8c89-45155e55f680','true','userinfo.token.claim'),('4a4bf29e-6de8-4141-b4a5-77cf62e15252','true','access.token.claim'),('4a4bf29e-6de8-4141-b4a5-77cf62e15252','email','claim.name'),('4a4bf29e-6de8-4141-b4a5-77cf62e15252','true','id.token.claim'),('4a4bf29e-6de8-4141-b4a5-77cf62e15252','String','jsonType.label'),('4a4bf29e-6de8-4141-b4a5-77cf62e15252','email','user.attribute'),('4a4bf29e-6de8-4141-b4a5-77cf62e15252','true','userinfo.token.claim'),('4cfb38ee-c76b-4e71-a893-88c824de7487','true','access.token.claim'),('4cfb38ee-c76b-4e71-a893-88c824de7487','given_name','claim.name'),('4cfb38ee-c76b-4e71-a893-88c824de7487','true','id.token.claim'),('4cfb38ee-c76b-4e71-a893-88c824de7487','String','jsonType.label'),('4cfb38ee-c76b-4e71-a893-88c824de7487','firstName','user.attribute'),('4cfb38ee-c76b-4e71-a893-88c824de7487','true','userinfo.token.claim'),('4f56c276-2518-4aaf-b449-d0e9baac3dba','true','access.token.claim'),('4f56c276-2518-4aaf-b449-d0e9baac3dba','phone_number_verified','claim.name'),('4f56c276-2518-4aaf-b449-d0e9baac3dba','true','id.token.claim'),('4f56c276-2518-4aaf-b449-d0e9baac3dba','boolean','jsonType.label'),('4f56c276-2518-4aaf-b449-d0e9baac3dba','phoneNumberVerified','user.attribute'),('4f56c276-2518-4aaf-b449-d0e9baac3dba','true','userinfo.token.claim'),('5441a18b-1473-4a26-a648-3f6c3ee5cb40','true','access.token.claim'),('5441a18b-1473-4a26-a648-3f6c3ee5cb40','profile','claim.name'),('5441a18b-1473-4a26-a648-3f6c3ee5cb40','true','id.token.claim'),('5441a18b-1473-4a26-a648-3f6c3ee5cb40','String','jsonType.label'),('5441a18b-1473-4a26-a648-3f6c3ee5cb40','profile','user.attribute'),('5441a18b-1473-4a26-a648-3f6c3ee5cb40','true','userinfo.token.claim'),('5aff14a7-012e-4097-ac43-101a8d6aaf04','true','access.token.claim'),('5aff14a7-012e-4097-ac43-101a8d6aaf04','website','claim.name'),('5aff14a7-012e-4097-ac43-101a8d6aaf04','true','id.token.claim'),('5aff14a7-012e-4097-ac43-101a8d6aaf04','String','jsonType.label'),('5aff14a7-012e-4097-ac43-101a8d6aaf04','website','user.attribute'),('5aff14a7-012e-4097-ac43-101a8d6aaf04','true','userinfo.token.claim'),('60b682a7-b238-4dbf-b4a2-10cfcbf78e53','true','access.token.claim'),('60b682a7-b238-4dbf-b4a2-10cfcbf78e53','realm_access.roles','claim.name'),('60b682a7-b238-4dbf-b4a2-10cfcbf78e53','String','jsonType.label'),('60b682a7-b238-4dbf-b4a2-10cfcbf78e53','true','multivalued'),('60b682a7-b238-4dbf-b4a2-10cfcbf78e53','foo','user.attribute'),('625803a4-22a6-4c44-9338-d865698221a6','true','access.token.claim'),('625803a4-22a6-4c44-9338-d865698221a6','upn','claim.name'),('625803a4-22a6-4c44-9338-d865698221a6','true','id.token.claim'),('625803a4-22a6-4c44-9338-d865698221a6','String','jsonType.label'),('625803a4-22a6-4c44-9338-d865698221a6','username','user.attribute'),('625803a4-22a6-4c44-9338-d865698221a6','true','userinfo.token.claim'),('65fda6df-3700-4cd6-aa9b-29ace9fa3c49','true','access.token.claim'),('65fda6df-3700-4cd6-aa9b-29ace9fa3c49','gender','claim.name'),('65fda6df-3700-4cd6-aa9b-29ace9fa3c49','true','id.token.claim'),('65fda6df-3700-4cd6-aa9b-29ace9fa3c49','String','jsonType.label'),('65fda6df-3700-4cd6-aa9b-29ace9fa3c49','gender','user.attribute'),('65fda6df-3700-4cd6-aa9b-29ace9fa3c49','true','userinfo.token.claim'),('66cc58ba-99d9-49ad-b7db-4e948f634062','true','access.token.claim'),('66cc58ba-99d9-49ad-b7db-4e948f634062','gender','claim.name'),('66cc58ba-99d9-49ad-b7db-4e948f634062','true','id.token.claim'),('66cc58ba-99d9-49ad-b7db-4e948f634062','String','jsonType.label'),('66cc58ba-99d9-49ad-b7db-4e948f634062','gender','user.attribute'),('66cc58ba-99d9-49ad-b7db-4e948f634062','true','userinfo.token.claim'),('66ccd308-f1bd-454a-b64b-1ab02c66f1ca','true','access.token.claim'),('66ccd308-f1bd-454a-b64b-1ab02c66f1ca','updated_at','claim.name'),('66ccd308-f1bd-454a-b64b-1ab02c66f1ca','true','id.token.claim'),('66ccd308-f1bd-454a-b64b-1ab02c66f1ca','String','jsonType.label'),('66ccd308-f1bd-454a-b64b-1ab02c66f1ca','updatedAt','user.attribute'),('66ccd308-f1bd-454a-b64b-1ab02c66f1ca','true','userinfo.token.claim'),('696a03c2-1a2b-41d7-b8af-7c70f09408f5','Role','attribute.name'),('696a03c2-1a2b-41d7-b8af-7c70f09408f5','Basic','attribute.nameformat'),('696a03c2-1a2b-41d7-b8af-7c70f09408f5','false','single'),('6a15a937-f212-465a-ae66-5e87c636bb56','true','access.token.claim'),('6a15a937-f212-465a-ae66-5e87c636bb56','phone_number','claim.name'),('6a15a937-f212-465a-ae66-5e87c636bb56','true','id.token.claim'),('6a15a937-f212-465a-ae66-5e87c636bb56','String','jsonType.label'),('6a15a937-f212-465a-ae66-5e87c636bb56','phoneNumber','user.attribute'),('6a15a937-f212-465a-ae66-5e87c636bb56','true','userinfo.token.claim'),('71e8357f-476f-46ef-ad82-33c5d8524951','true','access.token.claim'),('71e8357f-476f-46ef-ad82-33c5d8524951','picture','claim.name'),('71e8357f-476f-46ef-ad82-33c5d8524951','true','id.token.claim'),('71e8357f-476f-46ef-ad82-33c5d8524951','String','jsonType.label'),('71e8357f-476f-46ef-ad82-33c5d8524951','picture','user.attribute'),('71e8357f-476f-46ef-ad82-33c5d8524951','true','userinfo.token.claim'),('785fba6a-28e2-419e-aaf2-245ac1722bc1','true','access.token.claim'),('785fba6a-28e2-419e-aaf2-245ac1722bc1','true','id.token.claim'),('785fba6a-28e2-419e-aaf2-245ac1722bc1','true','userinfo.token.claim'),('7c01eb41-4481-40d7-ab7a-20633d511917','true','access.token.claim'),('7c01eb41-4481-40d7-ab7a-20633d511917','true','id.token.claim'),('7c01eb41-4481-40d7-ab7a-20633d511917','country','user.attribute.country'),('7c01eb41-4481-40d7-ab7a-20633d511917','formatted','user.attribute.formatted'),('7c01eb41-4481-40d7-ab7a-20633d511917','locality','user.attribute.locality'),('7c01eb41-4481-40d7-ab7a-20633d511917','postal_code','user.attribute.postal_code'),('7c01eb41-4481-40d7-ab7a-20633d511917','region','user.attribute.region'),('7c01eb41-4481-40d7-ab7a-20633d511917','street','user.attribute.street'),('7c01eb41-4481-40d7-ab7a-20633d511917','true','userinfo.token.claim'),('80ee0847-5da0-4dbc-b443-97c4b84ff75f','true','access.token.claim'),('80ee0847-5da0-4dbc-b443-97c4b84ff75f','birthdate','claim.name'),('80ee0847-5da0-4dbc-b443-97c4b84ff75f','true','id.token.claim'),('80ee0847-5da0-4dbc-b443-97c4b84ff75f','String','jsonType.label'),('80ee0847-5da0-4dbc-b443-97c4b84ff75f','birthdate','user.attribute'),('80ee0847-5da0-4dbc-b443-97c4b84ff75f','true','userinfo.token.claim'),('8161e1c4-56d4-49c1-94be-d60f6dad1edd','true','access.token.claim'),('8161e1c4-56d4-49c1-94be-d60f6dad1edd','middle_name','claim.name'),('8161e1c4-56d4-49c1-94be-d60f6dad1edd','true','id.token.claim'),('8161e1c4-56d4-49c1-94be-d60f6dad1edd','String','jsonType.label'),('8161e1c4-56d4-49c1-94be-d60f6dad1edd','middleName','user.attribute'),('8161e1c4-56d4-49c1-94be-d60f6dad1edd','true','userinfo.token.claim'),('85b1dd59-436f-4696-8aed-429a9cdb0d7a','true','access.token.claim'),('85b1dd59-436f-4696-8aed-429a9cdb0d7a','preferred_username','claim.name'),('85b1dd59-436f-4696-8aed-429a9cdb0d7a','true','id.token.claim'),('85b1dd59-436f-4696-8aed-429a9cdb0d7a','String','jsonType.label'),('85b1dd59-436f-4696-8aed-429a9cdb0d7a','username','user.attribute'),('85b1dd59-436f-4696-8aed-429a9cdb0d7a','true','userinfo.token.claim'),('87a2017c-4027-4d35-904c-3907fac2d342','true','access.token.claim'),('87a2017c-4027-4d35-904c-3907fac2d342','groups','claim.name'),('87a2017c-4027-4d35-904c-3907fac2d342','true','id.token.claim'),('87a2017c-4027-4d35-904c-3907fac2d342','String','jsonType.label'),('87a2017c-4027-4d35-904c-3907fac2d342','true','multivalued'),('87a2017c-4027-4d35-904c-3907fac2d342','foo','user.attribute'),('87a2017c-4027-4d35-904c-3907fac2d342','true','userinfo.token.claim'),('9e15a34f-3e2d-4c81-bb5b-f7a535cdbe97','true','access.token.claim'),('9e15a34f-3e2d-4c81-bb5b-f7a535cdbe97','nickname','claim.name'),('9e15a34f-3e2d-4c81-bb5b-f7a535cdbe97','true','id.token.claim'),('9e15a34f-3e2d-4c81-bb5b-f7a535cdbe97','String','jsonType.label'),('9e15a34f-3e2d-4c81-bb5b-f7a535cdbe97','nickname','user.attribute'),('9e15a34f-3e2d-4c81-bb5b-f7a535cdbe97','true','userinfo.token.claim'),('a57b4d3d-ca1d-4beb-84ce-6adb8a7621d1','true','access.token.claim'),('a57b4d3d-ca1d-4beb-84ce-6adb8a7621d1','profile','claim.name'),('a57b4d3d-ca1d-4beb-84ce-6adb8a7621d1','true','id.token.claim'),('a57b4d3d-ca1d-4beb-84ce-6adb8a7621d1','String','jsonType.label'),('a57b4d3d-ca1d-4beb-84ce-6adb8a7621d1','profile','user.attribute'),('a57b4d3d-ca1d-4beb-84ce-6adb8a7621d1','true','userinfo.token.claim'),('a6aa1859-410f-4b14-bc70-350689a2504e','true','access.token.claim'),('a6aa1859-410f-4b14-bc70-350689a2504e','birthdate','claim.name'),('a6aa1859-410f-4b14-bc70-350689a2504e','true','id.token.claim'),('a6aa1859-410f-4b14-bc70-350689a2504e','String','jsonType.label'),('a6aa1859-410f-4b14-bc70-350689a2504e','birthdate','user.attribute'),('a6aa1859-410f-4b14-bc70-350689a2504e','true','userinfo.token.claim'),('a9603ebc-8d23-45ff-b073-5b57d5159c8e','true','access.token.claim'),('a9603ebc-8d23-45ff-b073-5b57d5159c8e','nickname','claim.name'),('a9603ebc-8d23-45ff-b073-5b57d5159c8e','true','id.token.claim'),('a9603ebc-8d23-45ff-b073-5b57d5159c8e','String','jsonType.label'),('a9603ebc-8d23-45ff-b073-5b57d5159c8e','nickname','user.attribute'),('a9603ebc-8d23-45ff-b073-5b57d5159c8e','true','userinfo.token.claim'),('ab4f6ce2-fd08-43c9-8a16-c383d415a40e','true','access.token.claim'),('ab4f6ce2-fd08-43c9-8a16-c383d415a40e','given_name','claim.name'),('ab4f6ce2-fd08-43c9-8a16-c383d415a40e','true','id.token.claim'),('ab4f6ce2-fd08-43c9-8a16-c383d415a40e','String','jsonType.label'),('ab4f6ce2-fd08-43c9-8a16-c383d415a40e','firstName','user.attribute'),('ab4f6ce2-fd08-43c9-8a16-c383d415a40e','true','userinfo.token.claim'),('adfa6519-6bfb-4804-9b9b-67809d4159f2','Role','attribute.name'),('adfa6519-6bfb-4804-9b9b-67809d4159f2','Basic','attribute.nameformat'),('adfa6519-6bfb-4804-9b9b-67809d4159f2','false','single'),('ae27457a-a1e7-44ce-9b20-267ed969770d','true','access.token.claim'),('ae27457a-a1e7-44ce-9b20-267ed969770d','groups','claim.name'),('ae27457a-a1e7-44ce-9b20-267ed969770d','true','id.token.claim'),('ae27457a-a1e7-44ce-9b20-267ed969770d','String','jsonType.label'),('ae27457a-a1e7-44ce-9b20-267ed969770d','true','multivalued'),('ae27457a-a1e7-44ce-9b20-267ed969770d','foo','user.attribute'),('b35762ca-7c17-4708-8d21-5bc5c9945c98','true','access.token.claim'),('b35762ca-7c17-4708-8d21-5bc5c9945c98','resource_access.${client_id}.roles','claim.name'),('b35762ca-7c17-4708-8d21-5bc5c9945c98','String','jsonType.label'),('b35762ca-7c17-4708-8d21-5bc5c9945c98','true','multivalued'),('b35762ca-7c17-4708-8d21-5bc5c9945c98','foo','user.attribute'),('b459c737-3dc3-46fa-9cc6-f027949754c0','true','access.token.claim'),('b459c737-3dc3-46fa-9cc6-f027949754c0','phone_number','claim.name'),('b459c737-3dc3-46fa-9cc6-f027949754c0','true','id.token.claim'),('b459c737-3dc3-46fa-9cc6-f027949754c0','String','jsonType.label'),('b459c737-3dc3-46fa-9cc6-f027949754c0','phoneNumber','user.attribute'),('b459c737-3dc3-46fa-9cc6-f027949754c0','true','userinfo.token.claim'),('b5f331d7-d567-4eaa-990a-3ffdf5d931cb','true','access.token.claim'),('b5f331d7-d567-4eaa-990a-3ffdf5d931cb','updated_at','claim.name'),('b5f331d7-d567-4eaa-990a-3ffdf5d931cb','true','id.token.claim'),('b5f331d7-d567-4eaa-990a-3ffdf5d931cb','String','jsonType.label'),('b5f331d7-d567-4eaa-990a-3ffdf5d931cb','updatedAt','user.attribute'),('b5f331d7-d567-4eaa-990a-3ffdf5d931cb','true','userinfo.token.claim'),('b705542e-7227-4e59-9a39-977b3351172e','true','access.token.claim'),('b705542e-7227-4e59-9a39-977b3351172e','email_verified','claim.name'),('b705542e-7227-4e59-9a39-977b3351172e','true','id.token.claim'),('b705542e-7227-4e59-9a39-977b3351172e','boolean','jsonType.label'),('b705542e-7227-4e59-9a39-977b3351172e','emailVerified','user.attribute'),('b705542e-7227-4e59-9a39-977b3351172e','true','userinfo.token.claim'),('be44dbbf-dabe-493e-9032-29d5f6ec1ff9','true','access.token.claim'),('be44dbbf-dabe-493e-9032-29d5f6ec1ff9','picture','claim.name'),('be44dbbf-dabe-493e-9032-29d5f6ec1ff9','true','id.token.claim'),('be44dbbf-dabe-493e-9032-29d5f6ec1ff9','String','jsonType.label'),('be44dbbf-dabe-493e-9032-29d5f6ec1ff9','picture','user.attribute'),('be44dbbf-dabe-493e-9032-29d5f6ec1ff9','true','userinfo.token.claim'),('c40a0475-73ee-479d-bb04-68d9e1b582cf','true','access.token.claim'),('c40a0475-73ee-479d-bb04-68d9e1b582cf','upn','claim.name'),('c40a0475-73ee-479d-bb04-68d9e1b582cf','true','id.token.claim'),('c40a0475-73ee-479d-bb04-68d9e1b582cf','String','jsonType.label'),('c40a0475-73ee-479d-bb04-68d9e1b582cf','username','user.attribute'),('c40a0475-73ee-479d-bb04-68d9e1b582cf','true','userinfo.token.claim'),('c82c30d6-ab74-4555-83e2-f41fe726ac3a','true','access.token.claim'),('c82c30d6-ab74-4555-83e2-f41fe726ac3a','email','claim.name'),('c82c30d6-ab74-4555-83e2-f41fe726ac3a','true','id.token.claim'),('c82c30d6-ab74-4555-83e2-f41fe726ac3a','String','jsonType.label'),('c82c30d6-ab74-4555-83e2-f41fe726ac3a','email','user.attribute'),('c82c30d6-ab74-4555-83e2-f41fe726ac3a','true','userinfo.token.claim'),('d697a281-b936-459f-a05c-5d24a99ceb19','true','access.token.claim'),('d697a281-b936-459f-a05c-5d24a99ceb19','email_verified','claim.name'),('d697a281-b936-459f-a05c-5d24a99ceb19','true','id.token.claim'),('d697a281-b936-459f-a05c-5d24a99ceb19','boolean','jsonType.label'),('d697a281-b936-459f-a05c-5d24a99ceb19','emailVerified','user.attribute'),('d697a281-b936-459f-a05c-5d24a99ceb19','true','userinfo.token.claim'),('db2e520b-a53e-47cf-96d2-07cb714aacba','true','access.token.claim'),('db2e520b-a53e-47cf-96d2-07cb714aacba','true','id.token.claim'),('db2e520b-a53e-47cf-96d2-07cb714aacba','true','userinfo.token.claim'),('dee3763a-9983-412d-b846-e87eed41f2db','true','access.token.claim'),('dee3763a-9983-412d-b846-e87eed41f2db','locale','claim.name'),('dee3763a-9983-412d-b846-e87eed41f2db','true','id.token.claim'),('dee3763a-9983-412d-b846-e87eed41f2db','String','jsonType.label'),('dee3763a-9983-412d-b846-e87eed41f2db','locale','user.attribute'),('dee3763a-9983-412d-b846-e87eed41f2db','true','userinfo.token.claim'),('e7777acf-d9f9-4968-9b37-f0924b4628d7','true','access.token.claim'),('e7777acf-d9f9-4968-9b37-f0924b4628d7','website','claim.name'),('e7777acf-d9f9-4968-9b37-f0924b4628d7','true','id.token.claim'),('e7777acf-d9f9-4968-9b37-f0924b4628d7','String','jsonType.label'),('e7777acf-d9f9-4968-9b37-f0924b4628d7','website','user.attribute'),('e7777acf-d9f9-4968-9b37-f0924b4628d7','true','userinfo.token.claim'),('fb9e50f2-80b6-497b-8255-f0740a126db4','true','access.token.claim'),('fb9e50f2-80b6-497b-8255-f0740a126db4','zoneinfo','claim.name'),('fb9e50f2-80b6-497b-8255-f0740a126db4','true','id.token.claim'),('fb9e50f2-80b6-497b-8255-f0740a126db4','String','jsonType.label'),('fb9e50f2-80b6-497b-8255-f0740a126db4','zoneinfo','user.attribute'),('fb9e50f2-80b6-497b-8255-f0740a126db4','true','userinfo.token.claim'),('fdb8d711-44bf-4332-9273-31c4c19cd6bd','true','access.token.claim'),('fdb8d711-44bf-4332-9273-31c4c19cd6bd','family_name','claim.name'),('fdb8d711-44bf-4332-9273-31c4c19cd6bd','true','id.token.claim'),('fdb8d711-44bf-4332-9273-31c4c19cd6bd','String','jsonType.label'),('fdb8d711-44bf-4332-9273-31c4c19cd6bd','lastName','user.attribute'),('fdb8d711-44bf-4332-9273-31c4c19cd6bd','true','userinfo.token.claim');
/*!40000 ALTER TABLE `PROTOCOL_MAPPER_CONFIG` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REALM`
--

DROP TABLE IF EXISTS `REALM`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REALM` (
  `ID` varchar(36) NOT NULL,
  `ACCESS_CODE_LIFESPAN` int DEFAULT NULL,
  `USER_ACTION_LIFESPAN` int DEFAULT NULL,
  `ACCESS_TOKEN_LIFESPAN` int DEFAULT NULL,
  `ACCOUNT_THEME` varchar(255) DEFAULT NULL,
  `ADMIN_THEME` varchar(255) DEFAULT NULL,
  `EMAIL_THEME` varchar(255) DEFAULT NULL,
  `ENABLED` bit(1) NOT NULL DEFAULT b'0',
  `EVENTS_ENABLED` bit(1) NOT NULL DEFAULT b'0',
  `EVENTS_EXPIRATION` bigint DEFAULT NULL,
  `LOGIN_THEME` varchar(255) DEFAULT NULL,
  `NAME` varchar(255) DEFAULT NULL,
  `NOT_BEFORE` int DEFAULT NULL,
  `PASSWORD_POLICY` text,
  `REGISTRATION_ALLOWED` bit(1) NOT NULL DEFAULT b'0',
  `REMEMBER_ME` bit(1) NOT NULL DEFAULT b'0',
  `RESET_PASSWORD_ALLOWED` bit(1) NOT NULL DEFAULT b'0',
  `SOCIAL` bit(1) NOT NULL DEFAULT b'0',
  `SSL_REQUIRED` varchar(255) DEFAULT NULL,
  `SSO_IDLE_TIMEOUT` int DEFAULT NULL,
  `SSO_MAX_LIFESPAN` int DEFAULT NULL,
  `UPDATE_PROFILE_ON_SOC_LOGIN` bit(1) NOT NULL DEFAULT b'0',
  `VERIFY_EMAIL` bit(1) NOT NULL DEFAULT b'0',
  `MASTER_ADMIN_CLIENT` varchar(36) DEFAULT NULL,
  `LOGIN_LIFESPAN` int DEFAULT NULL,
  `INTERNATIONALIZATION_ENABLED` bit(1) NOT NULL DEFAULT b'0',
  `DEFAULT_LOCALE` varchar(255) DEFAULT NULL,
  `REG_EMAIL_AS_USERNAME` bit(1) NOT NULL DEFAULT b'0',
  `ADMIN_EVENTS_ENABLED` bit(1) NOT NULL DEFAULT b'0',
  `ADMIN_EVENTS_DETAILS_ENABLED` bit(1) NOT NULL DEFAULT b'0',
  `EDIT_USERNAME_ALLOWED` bit(1) NOT NULL DEFAULT b'0',
  `OTP_POLICY_COUNTER` int DEFAULT '0',
  `OTP_POLICY_WINDOW` int DEFAULT '1',
  `OTP_POLICY_PERIOD` int DEFAULT '30',
  `OTP_POLICY_DIGITS` int DEFAULT '6',
  `OTP_POLICY_ALG` varchar(36) DEFAULT 'HmacSHA1',
  `OTP_POLICY_TYPE` varchar(36) DEFAULT 'totp',
  `BROWSER_FLOW` varchar(36) DEFAULT NULL,
  `REGISTRATION_FLOW` varchar(36) DEFAULT NULL,
  `DIRECT_GRANT_FLOW` varchar(36) DEFAULT NULL,
  `RESET_CREDENTIALS_FLOW` varchar(36) DEFAULT NULL,
  `CLIENT_AUTH_FLOW` varchar(36) DEFAULT NULL,
  `OFFLINE_SESSION_IDLE_TIMEOUT` int DEFAULT '0',
  `REVOKE_REFRESH_TOKEN` bit(1) NOT NULL DEFAULT b'0',
  `ACCESS_TOKEN_LIFE_IMPLICIT` int DEFAULT '0',
  `LOGIN_WITH_EMAIL_ALLOWED` bit(1) NOT NULL DEFAULT b'1',
  `DUPLICATE_EMAILS_ALLOWED` bit(1) NOT NULL DEFAULT b'0',
  `DOCKER_AUTH_FLOW` varchar(36) DEFAULT NULL,
  `REFRESH_TOKEN_MAX_REUSE` int DEFAULT '0',
  `ALLOW_USER_MANAGED_ACCESS` bit(1) NOT NULL DEFAULT b'0',
  `SSO_MAX_LIFESPAN_REMEMBER_ME` int NOT NULL,
  `SSO_IDLE_TIMEOUT_REMEMBER_ME` int NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `UK_ORVSDMLA56612EAEFIQ6WL5OI` (`NAME`),
  KEY `IDX_REALM_MASTER_ADM_CLI` (`MASTER_ADMIN_CLIENT`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REALM`
--

LOCK TABLES `REALM` WRITE;
/*!40000 ALTER TABLE `REALM` DISABLE KEYS */;
INSERT INTO `REALM` VALUES ('master',60,300,60,NULL,NULL,NULL,_binary '',_binary '\0',0,NULL,'master',0,NULL,_binary '\0',_binary '\0',_binary '\0',_binary '\0','EXTERNAL',1800,36000,_binary '\0',_binary '\0','3e40f193-9407-4729-88c2-95fcc3ab220f',1800,_binary '\0',NULL,_binary '\0',_binary '\0',_binary '\0',_binary '\0',0,1,30,6,'HmacSHA1','totp','c0344e9e-b3cd-4468-9248-3fb84023a775','ef6ff606-c66a-4b1d-801c-e966c33c1b2a','08d6c5ff-abc4-4d65-b9fc-e3372d62fcc0','d04b00e9-0d38-42cf-b01e-bb1186506485','92431b5a-91d0-4389-bb3e-2f5b3b4aee59',2592000,_binary '\0',900,_binary '',_binary '\0','4ab909dd-030d-43a1-a69f-ce975803d511',0,_binary '\0',0,0),('WESkit',60,300,300,NULL,NULL,NULL,_binary '',_binary '\0',0,NULL,'WESkit',0,NULL,_binary '\0',_binary '\0',_binary '\0',_binary '\0','EXTERNAL',1800,36000,_binary '\0',_binary '\0','69131d51-8b86-4470-a07c-a51305df8782',1800,_binary '\0',NULL,_binary '\0',_binary '\0',_binary '\0',_binary '\0',0,1,30,6,'HmacSHA1','totp','92ed5a7a-96ae-4cb9-b56d-eb20a9dffcbb','93343dd1-d31e-4814-a76b-0ef0f214fd2c','88aea7e1-06d3-48a2-bc87-2b0bee543f11','51f3e5bf-c65b-4e46-8c25-6bd8f6a4c155','6ad3a3f0-62ca-45cc-a0e8-593e58c987c0',2592000,_binary '\0',900,_binary '',_binary '\0','30d3b23c-fb6d-41e0-afd8-f11714a972cb',0,_binary '\0',0,0);
/*!40000 ALTER TABLE `REALM` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REALM_ATTRIBUTE`
--

DROP TABLE IF EXISTS `REALM_ATTRIBUTE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REALM_ATTRIBUTE` (
  `NAME` varchar(255) NOT NULL,
  `VALUE` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`NAME`,`REALM_ID`),
  KEY `IDX_REALM_ATTR_REALM` (`REALM_ID`),
  CONSTRAINT `FK_8SHXD6L3E9ATQUKACXGPFFPTW` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REALM_ATTRIBUTE`
--

LOCK TABLES `REALM_ATTRIBUTE` WRITE;
/*!40000 ALTER TABLE `REALM_ATTRIBUTE` DISABLE KEYS */;
INSERT INTO `REALM_ATTRIBUTE` VALUES ('_browser_header.contentSecurityPolicy','frame-src \'self\'; frame-ancestors \'self\'; object-src \'none\';','master'),('_browser_header.contentSecurityPolicy','frame-src \'self\'; frame-ancestors \'self\'; object-src \'none\';','WESkit'),('_browser_header.contentSecurityPolicyReportOnly','','master'),('_browser_header.contentSecurityPolicyReportOnly','','WESkit'),('_browser_header.strictTransportSecurity','max-age=31536000; includeSubDomains','master'),('_browser_header.strictTransportSecurity','max-age=31536000; includeSubDomains','WESkit'),('_browser_header.xContentTypeOptions','nosniff','master'),('_browser_header.xContentTypeOptions','nosniff','WESkit'),('_browser_header.xFrameOptions','SAMEORIGIN','master'),('_browser_header.xFrameOptions','SAMEORIGIN','WESkit'),('_browser_header.xRobotsTag','none','master'),('_browser_header.xRobotsTag','none','WESkit'),('_browser_header.xXSSProtection','1; mode=block','master'),('_browser_header.xXSSProtection','1; mode=block','WESkit'),('actionTokenGeneratedByAdminLifespan','43200','WESkit'),('actionTokenGeneratedByUserLifespan','300','WESkit'),('bruteForceProtected','false','master'),('bruteForceProtected','false','WESkit'),('clientOfflineSessionIdleTimeout','0','WESkit'),('clientOfflineSessionMaxLifespan','0','WESkit'),('clientSessionIdleTimeout','0','WESkit'),('clientSessionMaxLifespan','0','WESkit'),('displayName','Keycloak','master'),('displayName','WESkit','WESkit'),('displayNameHtml','<div class=\"kc-logo-text\"><span>Keycloak</span></div>','master'),('displayNameHtml','<span>WESkit</span>','WESkit'),('failureFactor','30','master'),('failureFactor','30','WESkit'),('frontendUrl','','WESkit'),('maxDeltaTimeSeconds','43200','master'),('maxDeltaTimeSeconds','43200','WESkit'),('maxFailureWaitSeconds','900','master'),('maxFailureWaitSeconds','900','WESkit'),('minimumQuickLoginWaitSeconds','60','master'),('minimumQuickLoginWaitSeconds','60','WESkit'),('offlineSessionMaxLifespan','5184000','master'),('offlineSessionMaxLifespan','5184000','WESkit'),('offlineSessionMaxLifespanEnabled','false','master'),('offlineSessionMaxLifespanEnabled','false','WESkit'),('permanentLockout','false','master'),('permanentLockout','false','WESkit'),('quickLoginCheckMilliSeconds','1000','master'),('quickLoginCheckMilliSeconds','1000','WESkit'),('waitIncrementSeconds','60','master'),('waitIncrementSeconds','60','WESkit'),('webAuthnPolicyAttestationConveyancePreference','not specified','WESkit'),('webAuthnPolicyAttestationConveyancePreferencePasswordless','not specified','WESkit'),('webAuthnPolicyAuthenticatorAttachment','not specified','WESkit'),('webAuthnPolicyAuthenticatorAttachmentPasswordless','not specified','WESkit'),('webAuthnPolicyAvoidSameAuthenticatorRegister','false','WESkit'),('webAuthnPolicyAvoidSameAuthenticatorRegisterPasswordless','false','WESkit'),('webAuthnPolicyCreateTimeout','0','WESkit'),('webAuthnPolicyCreateTimeoutPasswordless','0','WESkit'),('webAuthnPolicyRequireResidentKey','not specified','WESkit'),('webAuthnPolicyRequireResidentKeyPasswordless','not specified','WESkit'),('webAuthnPolicyRpEntityName','keycloak','WESkit'),('webAuthnPolicyRpEntityNamePasswordless','keycloak','WESkit'),('webAuthnPolicyRpId','','WESkit'),('webAuthnPolicyRpIdPasswordless','','WESkit'),('webAuthnPolicySignatureAlgorithms','ES256','WESkit'),('webAuthnPolicySignatureAlgorithmsPasswordless','ES256','WESkit'),('webAuthnPolicyUserVerificationRequirement','not specified','WESkit'),('webAuthnPolicyUserVerificationRequirementPasswordless','not specified','WESkit');
/*!40000 ALTER TABLE `REALM_ATTRIBUTE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REALM_DEFAULT_GROUPS`
--

DROP TABLE IF EXISTS `REALM_DEFAULT_GROUPS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REALM_DEFAULT_GROUPS` (
  `REALM_ID` varchar(36) NOT NULL,
  `GROUP_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`REALM_ID`,`GROUP_ID`),
  UNIQUE KEY `CON_GROUP_ID_DEF_GROUPS` (`GROUP_ID`),
  KEY `IDX_REALM_DEF_GRP_REALM` (`REALM_ID`),
  CONSTRAINT `FK_DEF_GROUPS_REALM` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REALM_DEFAULT_GROUPS`
--

LOCK TABLES `REALM_DEFAULT_GROUPS` WRITE;
/*!40000 ALTER TABLE `REALM_DEFAULT_GROUPS` DISABLE KEYS */;
/*!40000 ALTER TABLE `REALM_DEFAULT_GROUPS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REALM_DEFAULT_ROLES`
--

DROP TABLE IF EXISTS `REALM_DEFAULT_ROLES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REALM_DEFAULT_ROLES` (
  `REALM_ID` varchar(36) NOT NULL,
  `ROLE_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`REALM_ID`,`ROLE_ID`),
  UNIQUE KEY `UK_H4WPD7W4HSOOLNI3H0SW7BTJE` (`ROLE_ID`),
  KEY `IDX_REALM_DEF_ROLES_REALM` (`REALM_ID`),
  CONSTRAINT `FK_EVUDB1PPW84OXFAX2DRS03ICC` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REALM_DEFAULT_ROLES`
--

LOCK TABLES `REALM_DEFAULT_ROLES` WRITE;
/*!40000 ALTER TABLE `REALM_DEFAULT_ROLES` DISABLE KEYS */;
INSERT INTO `REALM_DEFAULT_ROLES` VALUES ('master','02a5d5df-98a6-4b2d-8bbe-bde39eec7995'),('WESkit','4d51c469-5b72-41ad-b987-b414839904aa'),('WESkit','52a3415d-65a9-4314-8805-c85ca05b55d6'),('master','cbc5dbe2-ac59-4b57-a641-387d94e759c6');
/*!40000 ALTER TABLE `REALM_DEFAULT_ROLES` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REALM_ENABLED_EVENT_TYPES`
--

DROP TABLE IF EXISTS `REALM_ENABLED_EVENT_TYPES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REALM_ENABLED_EVENT_TYPES` (
  `REALM_ID` varchar(36) NOT NULL,
  `VALUE` varchar(255) NOT NULL,
  PRIMARY KEY (`REALM_ID`,`VALUE`),
  KEY `IDX_REALM_EVT_TYPES_REALM` (`REALM_ID`),
  CONSTRAINT `FK_H846O4H0W8EPX5NWEDRF5Y69J` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REALM_ENABLED_EVENT_TYPES`
--

LOCK TABLES `REALM_ENABLED_EVENT_TYPES` WRITE;
/*!40000 ALTER TABLE `REALM_ENABLED_EVENT_TYPES` DISABLE KEYS */;
/*!40000 ALTER TABLE `REALM_ENABLED_EVENT_TYPES` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REALM_EVENTS_LISTENERS`
--

DROP TABLE IF EXISTS `REALM_EVENTS_LISTENERS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REALM_EVENTS_LISTENERS` (
  `REALM_ID` varchar(36) NOT NULL,
  `VALUE` varchar(255) NOT NULL,
  PRIMARY KEY (`REALM_ID`,`VALUE`),
  KEY `IDX_REALM_EVT_LIST_REALM` (`REALM_ID`),
  CONSTRAINT `FK_H846O4H0W8EPX5NXEV9F5Y69J` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REALM_EVENTS_LISTENERS`
--

LOCK TABLES `REALM_EVENTS_LISTENERS` WRITE;
/*!40000 ALTER TABLE `REALM_EVENTS_LISTENERS` DISABLE KEYS */;
INSERT INTO `REALM_EVENTS_LISTENERS` VALUES ('master','jboss-logging'),('WESkit','jboss-logging');
/*!40000 ALTER TABLE `REALM_EVENTS_LISTENERS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REALM_LOCALIZATIONS`
--

DROP TABLE IF EXISTS `REALM_LOCALIZATIONS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REALM_LOCALIZATIONS` (
  `REALM_ID` varchar(255) NOT NULL,
  `LOCALE` varchar(255) NOT NULL,
  `TEXTS` longtext NOT NULL,
  PRIMARY KEY (`REALM_ID`,`LOCALE`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REALM_LOCALIZATIONS`
--

LOCK TABLES `REALM_LOCALIZATIONS` WRITE;
/*!40000 ALTER TABLE `REALM_LOCALIZATIONS` DISABLE KEYS */;
/*!40000 ALTER TABLE `REALM_LOCALIZATIONS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REALM_REQUIRED_CREDENTIAL`
--

DROP TABLE IF EXISTS `REALM_REQUIRED_CREDENTIAL`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REALM_REQUIRED_CREDENTIAL` (
  `TYPE` varchar(255) NOT NULL,
  `FORM_LABEL` varchar(255) DEFAULT NULL,
  `INPUT` bit(1) NOT NULL DEFAULT b'0',
  `SECRET` bit(1) NOT NULL DEFAULT b'0',
  `REALM_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`REALM_ID`,`TYPE`),
  CONSTRAINT `FK_5HG65LYBEVAVKQFKI3KPONH9V` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REALM_REQUIRED_CREDENTIAL`
--

LOCK TABLES `REALM_REQUIRED_CREDENTIAL` WRITE;
/*!40000 ALTER TABLE `REALM_REQUIRED_CREDENTIAL` DISABLE KEYS */;
INSERT INTO `REALM_REQUIRED_CREDENTIAL` VALUES ('password','password',_binary '',_binary '','master'),('password','password',_binary '',_binary '','WESkit');
/*!40000 ALTER TABLE `REALM_REQUIRED_CREDENTIAL` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REALM_SMTP_CONFIG`
--

DROP TABLE IF EXISTS `REALM_SMTP_CONFIG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REALM_SMTP_CONFIG` (
  `REALM_ID` varchar(36) NOT NULL,
  `VALUE` varchar(255) DEFAULT NULL,
  `NAME` varchar(255) NOT NULL,
  PRIMARY KEY (`REALM_ID`,`NAME`),
  CONSTRAINT `FK_70EJ8XDXGXD0B9HH6180IRR0O` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REALM_SMTP_CONFIG`
--

LOCK TABLES `REALM_SMTP_CONFIG` WRITE;
/*!40000 ALTER TABLE `REALM_SMTP_CONFIG` DISABLE KEYS */;
/*!40000 ALTER TABLE `REALM_SMTP_CONFIG` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REALM_SUPPORTED_LOCALES`
--

DROP TABLE IF EXISTS `REALM_SUPPORTED_LOCALES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REALM_SUPPORTED_LOCALES` (
  `REALM_ID` varchar(36) NOT NULL,
  `VALUE` varchar(255) NOT NULL,
  PRIMARY KEY (`REALM_ID`,`VALUE`),
  KEY `IDX_REALM_SUPP_LOCAL_REALM` (`REALM_ID`),
  CONSTRAINT `FK_SUPPORTED_LOCALES_REALM` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REALM_SUPPORTED_LOCALES`
--

LOCK TABLES `REALM_SUPPORTED_LOCALES` WRITE;
/*!40000 ALTER TABLE `REALM_SUPPORTED_LOCALES` DISABLE KEYS */;
/*!40000 ALTER TABLE `REALM_SUPPORTED_LOCALES` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REDIRECT_URIS`
--

DROP TABLE IF EXISTS `REDIRECT_URIS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REDIRECT_URIS` (
  `CLIENT_ID` varchar(36) NOT NULL,
  `VALUE` varchar(255) NOT NULL,
  PRIMARY KEY (`CLIENT_ID`,`VALUE`),
  KEY `IDX_REDIR_URI_CLIENT` (`CLIENT_ID`),
  CONSTRAINT `FK_1BURS8PB4OUJ97H5WUPPAHV9F` FOREIGN KEY (`CLIENT_ID`) REFERENCES `CLIENT` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REDIRECT_URIS`
--

LOCK TABLES `REDIRECT_URIS` WRITE;
/*!40000 ALTER TABLE `REDIRECT_URIS` DISABLE KEYS */;
INSERT INTO `REDIRECT_URIS` VALUES ('48ca4365-c4d8-477b-91ce-d3509dc77334','https://localhost:5000/*'),('4b528bc5-f5d0-446f-834d-5b834ea41103','https://localhost:5001/*'),('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a','/admin/master/console/*'),('5060e61b-233b-4347-94e2-4d84d3e67dcc','/realms/master/account/*'),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae','/admin/WESkit/console/*'),('77249ec3-5596-4d8b-a2d3-15604ca70de5','/realms/WESkit/account/*'),('e47088a1-3190-435b-a237-e4e0b50988d5','/realms/master/account/*'),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03','/realms/WESkit/account/*');
/*!40000 ALTER TABLE `REDIRECT_URIS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REQUIRED_ACTION_CONFIG`
--

DROP TABLE IF EXISTS `REQUIRED_ACTION_CONFIG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REQUIRED_ACTION_CONFIG` (
  `REQUIRED_ACTION_ID` varchar(36) NOT NULL,
  `VALUE` longtext,
  `NAME` varchar(255) NOT NULL,
  PRIMARY KEY (`REQUIRED_ACTION_ID`,`NAME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REQUIRED_ACTION_CONFIG`
--

LOCK TABLES `REQUIRED_ACTION_CONFIG` WRITE;
/*!40000 ALTER TABLE `REQUIRED_ACTION_CONFIG` DISABLE KEYS */;
/*!40000 ALTER TABLE `REQUIRED_ACTION_CONFIG` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `REQUIRED_ACTION_PROVIDER`
--

DROP TABLE IF EXISTS `REQUIRED_ACTION_PROVIDER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `REQUIRED_ACTION_PROVIDER` (
  `ID` varchar(36) NOT NULL,
  `ALIAS` varchar(255) DEFAULT NULL,
  `NAME` varchar(255) DEFAULT NULL,
  `REALM_ID` varchar(36) DEFAULT NULL,
  `ENABLED` bit(1) NOT NULL DEFAULT b'0',
  `DEFAULT_ACTION` bit(1) NOT NULL DEFAULT b'0',
  `PROVIDER_ID` varchar(255) DEFAULT NULL,
  `PRIORITY` int DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_REQ_ACT_PROV_REALM` (`REALM_ID`),
  CONSTRAINT `FK_REQ_ACT_REALM` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `REQUIRED_ACTION_PROVIDER`
--

LOCK TABLES `REQUIRED_ACTION_PROVIDER` WRITE;
/*!40000 ALTER TABLE `REQUIRED_ACTION_PROVIDER` DISABLE KEYS */;
INSERT INTO `REQUIRED_ACTION_PROVIDER` VALUES ('01854f6f-af28-4d3f-afb3-59cbfaad338a','UPDATE_PROFILE','Update Profile','master',_binary '',_binary '\0','UPDATE_PROFILE',40),('2283f8cb-392b-4f48-93fd-7a2df96946e5','UPDATE_PASSWORD','Update Password','master',_binary '',_binary '\0','UPDATE_PASSWORD',30),('335e9b4d-2288-4bb4-9bea-722cf116529b','update_user_locale','Update User Locale','master',_binary '',_binary '\0','update_user_locale',1000),('49d1df65-44a1-41c5-802d-8310b73f629f','VERIFY_EMAIL','Verify Email','WESkit',_binary '',_binary '\0','VERIFY_EMAIL',50),('51d3989a-32cf-4c96-a6e7-30c56c9977a7','delete_account','Delete Account','master',_binary '\0',_binary '\0','delete_account',60),('5fd3f8c8-e293-4a90-9dcd-a279c09da7a2','update_user_locale','Update User Locale','WESkit',_binary '',_binary '\0','update_user_locale',1000),('6d560f70-e0a8-4052-94bb-d31d480784e2','UPDATE_PASSWORD','Update Password','WESkit',_binary '',_binary '\0','UPDATE_PASSWORD',30),('98c0b9e0-ecb5-4842-ac64-5837044703b5','delete_account','Delete Account','WESkit',_binary '\0',_binary '\0','delete_account',60),('a8363bca-2d1d-49b3-84f9-16c7e91b11a3','UPDATE_PROFILE','Update Profile','WESkit',_binary '',_binary '\0','UPDATE_PROFILE',40),('c8387670-fd1d-4ee1-8357-fc92af8a78f7','terms_and_conditions','Terms and Conditions','master',_binary '\0',_binary '\0','terms_and_conditions',20),('cab03148-4264-46bc-b0a6-1e3ab8eb2efe','CONFIGURE_TOTP','Configure OTP','master',_binary '',_binary '\0','CONFIGURE_TOTP',10),('d46a7246-08da-4283-b362-2ea582587cb0','VERIFY_EMAIL','Verify Email','master',_binary '',_binary '\0','VERIFY_EMAIL',50),('dbd474ce-cbe1-4458-bdbd-cbb454f270d0','CONFIGURE_TOTP','Configure OTP','WESkit',_binary '',_binary '\0','CONFIGURE_TOTP',10),('fd515d2f-9492-4504-9501-a615acbae244','terms_and_conditions','Terms and Conditions','WESkit',_binary '\0',_binary '\0','terms_and_conditions',20);
/*!40000 ALTER TABLE `REQUIRED_ACTION_PROVIDER` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RESOURCE_ATTRIBUTE`
--

DROP TABLE IF EXISTS `RESOURCE_ATTRIBUTE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RESOURCE_ATTRIBUTE` (
  `ID` varchar(36) NOT NULL DEFAULT 'sybase-needs-something-here',
  `NAME` varchar(255) NOT NULL,
  `VALUE` varchar(255) DEFAULT NULL,
  `RESOURCE_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `FK_5HRM2VLF9QL5FU022KQEPOVBR` (`RESOURCE_ID`),
  CONSTRAINT `FK_5HRM2VLF9QL5FU022KQEPOVBR` FOREIGN KEY (`RESOURCE_ID`) REFERENCES `RESOURCE_SERVER_RESOURCE` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RESOURCE_ATTRIBUTE`
--

LOCK TABLES `RESOURCE_ATTRIBUTE` WRITE;
/*!40000 ALTER TABLE `RESOURCE_ATTRIBUTE` DISABLE KEYS */;
/*!40000 ALTER TABLE `RESOURCE_ATTRIBUTE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RESOURCE_POLICY`
--

DROP TABLE IF EXISTS `RESOURCE_POLICY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RESOURCE_POLICY` (
  `RESOURCE_ID` varchar(36) NOT NULL,
  `POLICY_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`RESOURCE_ID`,`POLICY_ID`),
  KEY `IDX_RES_POLICY_POLICY` (`POLICY_ID`),
  CONSTRAINT `FK_FRSRPOS53XCX4WNKOG82SSRFY` FOREIGN KEY (`RESOURCE_ID`) REFERENCES `RESOURCE_SERVER_RESOURCE` (`ID`),
  CONSTRAINT `FK_FRSRPP213XCX4WNKOG82SSRFY` FOREIGN KEY (`POLICY_ID`) REFERENCES `RESOURCE_SERVER_POLICY` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RESOURCE_POLICY`
--

LOCK TABLES `RESOURCE_POLICY` WRITE;
/*!40000 ALTER TABLE `RESOURCE_POLICY` DISABLE KEYS */;
/*!40000 ALTER TABLE `RESOURCE_POLICY` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RESOURCE_SCOPE`
--

DROP TABLE IF EXISTS `RESOURCE_SCOPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RESOURCE_SCOPE` (
  `RESOURCE_ID` varchar(36) NOT NULL,
  `SCOPE_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`RESOURCE_ID`,`SCOPE_ID`),
  KEY `IDX_RES_SCOPE_SCOPE` (`SCOPE_ID`),
  CONSTRAINT `FK_FRSRPOS13XCX4WNKOG82SSRFY` FOREIGN KEY (`RESOURCE_ID`) REFERENCES `RESOURCE_SERVER_RESOURCE` (`ID`),
  CONSTRAINT `FK_FRSRPS213XCX4WNKOG82SSRFY` FOREIGN KEY (`SCOPE_ID`) REFERENCES `RESOURCE_SERVER_SCOPE` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RESOURCE_SCOPE`
--

LOCK TABLES `RESOURCE_SCOPE` WRITE;
/*!40000 ALTER TABLE `RESOURCE_SCOPE` DISABLE KEYS */;
/*!40000 ALTER TABLE `RESOURCE_SCOPE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RESOURCE_SERVER`
--

DROP TABLE IF EXISTS `RESOURCE_SERVER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RESOURCE_SERVER` (
  `ID` varchar(36) NOT NULL,
  `ALLOW_RS_REMOTE_MGMT` bit(1) NOT NULL DEFAULT b'0',
  `POLICY_ENFORCE_MODE` varchar(15) NOT NULL,
  `DECISION_STRATEGY` tinyint NOT NULL DEFAULT '1',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RESOURCE_SERVER`
--

LOCK TABLES `RESOURCE_SERVER` WRITE;
/*!40000 ALTER TABLE `RESOURCE_SERVER` DISABLE KEYS */;
/*!40000 ALTER TABLE `RESOURCE_SERVER` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RESOURCE_SERVER_PERM_TICKET`
--

DROP TABLE IF EXISTS `RESOURCE_SERVER_PERM_TICKET`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RESOURCE_SERVER_PERM_TICKET` (
  `ID` varchar(36) NOT NULL,
  `OWNER` varchar(255) DEFAULT NULL,
  `REQUESTER` varchar(255) DEFAULT NULL,
  `CREATED_TIMESTAMP` bigint NOT NULL,
  `GRANTED_TIMESTAMP` bigint DEFAULT NULL,
  `RESOURCE_ID` varchar(36) NOT NULL,
  `SCOPE_ID` varchar(36) DEFAULT NULL,
  `RESOURCE_SERVER_ID` varchar(36) NOT NULL,
  `POLICY_ID` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `UK_FRSR6T700S9V50BU18WS5PMT` (`OWNER`,`REQUESTER`,`RESOURCE_SERVER_ID`,`RESOURCE_ID`,`SCOPE_ID`),
  KEY `FK_FRSRHO213XCX4WNKOG82SSPMT` (`RESOURCE_SERVER_ID`),
  KEY `FK_FRSRHO213XCX4WNKOG83SSPMT` (`RESOURCE_ID`),
  KEY `FK_FRSRHO213XCX4WNKOG84SSPMT` (`SCOPE_ID`),
  KEY `FK_FRSRPO2128CX4WNKOG82SSRFY` (`POLICY_ID`),
  CONSTRAINT `FK_FRSRHO213XCX4WNKOG82SSPMT` FOREIGN KEY (`RESOURCE_SERVER_ID`) REFERENCES `RESOURCE_SERVER` (`ID`),
  CONSTRAINT `FK_FRSRHO213XCX4WNKOG83SSPMT` FOREIGN KEY (`RESOURCE_ID`) REFERENCES `RESOURCE_SERVER_RESOURCE` (`ID`),
  CONSTRAINT `FK_FRSRHO213XCX4WNKOG84SSPMT` FOREIGN KEY (`SCOPE_ID`) REFERENCES `RESOURCE_SERVER_SCOPE` (`ID`),
  CONSTRAINT `FK_FRSRPO2128CX4WNKOG82SSRFY` FOREIGN KEY (`POLICY_ID`) REFERENCES `RESOURCE_SERVER_POLICY` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RESOURCE_SERVER_PERM_TICKET`
--

LOCK TABLES `RESOURCE_SERVER_PERM_TICKET` WRITE;
/*!40000 ALTER TABLE `RESOURCE_SERVER_PERM_TICKET` DISABLE KEYS */;
/*!40000 ALTER TABLE `RESOURCE_SERVER_PERM_TICKET` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RESOURCE_SERVER_POLICY`
--

DROP TABLE IF EXISTS `RESOURCE_SERVER_POLICY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RESOURCE_SERVER_POLICY` (
  `ID` varchar(36) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `DESCRIPTION` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `TYPE` varchar(255) NOT NULL,
  `DECISION_STRATEGY` varchar(20) DEFAULT NULL,
  `LOGIC` varchar(20) DEFAULT NULL,
  `RESOURCE_SERVER_ID` varchar(36) DEFAULT NULL,
  `OWNER` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `UK_FRSRPT700S9V50BU18WS5HA6` (`NAME`,`RESOURCE_SERVER_ID`),
  KEY `IDX_RES_SERV_POL_RES_SERV` (`RESOURCE_SERVER_ID`),
  CONSTRAINT `FK_FRSRPO213XCX4WNKOG82SSRFY` FOREIGN KEY (`RESOURCE_SERVER_ID`) REFERENCES `RESOURCE_SERVER` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RESOURCE_SERVER_POLICY`
--

LOCK TABLES `RESOURCE_SERVER_POLICY` WRITE;
/*!40000 ALTER TABLE `RESOURCE_SERVER_POLICY` DISABLE KEYS */;
/*!40000 ALTER TABLE `RESOURCE_SERVER_POLICY` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RESOURCE_SERVER_RESOURCE`
--

DROP TABLE IF EXISTS `RESOURCE_SERVER_RESOURCE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RESOURCE_SERVER_RESOURCE` (
  `ID` varchar(36) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `TYPE` varchar(255) DEFAULT NULL,
  `ICON_URI` varchar(255) DEFAULT NULL,
  `OWNER` varchar(255) DEFAULT NULL,
  `RESOURCE_SERVER_ID` varchar(36) DEFAULT NULL,
  `OWNER_MANAGED_ACCESS` bit(1) NOT NULL DEFAULT b'0',
  `DISPLAY_NAME` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `UK_FRSR6T700S9V50BU18WS5HA6` (`NAME`,`OWNER`,`RESOURCE_SERVER_ID`),
  KEY `IDX_RES_SRV_RES_RES_SRV` (`RESOURCE_SERVER_ID`),
  CONSTRAINT `FK_FRSRHO213XCX4WNKOG82SSRFY` FOREIGN KEY (`RESOURCE_SERVER_ID`) REFERENCES `RESOURCE_SERVER` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RESOURCE_SERVER_RESOURCE`
--

LOCK TABLES `RESOURCE_SERVER_RESOURCE` WRITE;
/*!40000 ALTER TABLE `RESOURCE_SERVER_RESOURCE` DISABLE KEYS */;
/*!40000 ALTER TABLE `RESOURCE_SERVER_RESOURCE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RESOURCE_SERVER_SCOPE`
--

DROP TABLE IF EXISTS `RESOURCE_SERVER_SCOPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RESOURCE_SERVER_SCOPE` (
  `ID` varchar(36) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `ICON_URI` varchar(255) DEFAULT NULL,
  `RESOURCE_SERVER_ID` varchar(36) DEFAULT NULL,
  `DISPLAY_NAME` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `UK_FRSRST700S9V50BU18WS5HA6` (`NAME`,`RESOURCE_SERVER_ID`),
  KEY `IDX_RES_SRV_SCOPE_RES_SRV` (`RESOURCE_SERVER_ID`),
  CONSTRAINT `FK_FRSRSO213XCX4WNKOG82SSRFY` FOREIGN KEY (`RESOURCE_SERVER_ID`) REFERENCES `RESOURCE_SERVER` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RESOURCE_SERVER_SCOPE`
--

LOCK TABLES `RESOURCE_SERVER_SCOPE` WRITE;
/*!40000 ALTER TABLE `RESOURCE_SERVER_SCOPE` DISABLE KEYS */;
/*!40000 ALTER TABLE `RESOURCE_SERVER_SCOPE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RESOURCE_URIS`
--

DROP TABLE IF EXISTS `RESOURCE_URIS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RESOURCE_URIS` (
  `RESOURCE_ID` varchar(36) NOT NULL,
  `VALUE` varchar(255) NOT NULL,
  PRIMARY KEY (`RESOURCE_ID`,`VALUE`),
  CONSTRAINT `FK_RESOURCE_SERVER_URIS` FOREIGN KEY (`RESOURCE_ID`) REFERENCES `RESOURCE_SERVER_RESOURCE` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RESOURCE_URIS`
--

LOCK TABLES `RESOURCE_URIS` WRITE;
/*!40000 ALTER TABLE `RESOURCE_URIS` DISABLE KEYS */;
/*!40000 ALTER TABLE `RESOURCE_URIS` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ROLE_ATTRIBUTE`
--

DROP TABLE IF EXISTS `ROLE_ATTRIBUTE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ROLE_ATTRIBUTE` (
  `ID` varchar(36) NOT NULL,
  `ROLE_ID` varchar(36) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `VALUE` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_ROLE_ATTRIBUTE` (`ROLE_ID`),
  CONSTRAINT `FK_ROLE_ATTRIBUTE_ID` FOREIGN KEY (`ROLE_ID`) REFERENCES `KEYCLOAK_ROLE` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ROLE_ATTRIBUTE`
--

LOCK TABLES `ROLE_ATTRIBUTE` WRITE;
/*!40000 ALTER TABLE `ROLE_ATTRIBUTE` DISABLE KEYS */;
/*!40000 ALTER TABLE `ROLE_ATTRIBUTE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SCOPE_MAPPING`
--

DROP TABLE IF EXISTS `SCOPE_MAPPING`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SCOPE_MAPPING` (
  `CLIENT_ID` varchar(36) NOT NULL,
  `ROLE_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`CLIENT_ID`,`ROLE_ID`),
  KEY `IDX_SCOPE_MAPPING_ROLE` (`ROLE_ID`),
  CONSTRAINT `FK_OUSE064PLMLR732LXJCN1Q5F1` FOREIGN KEY (`CLIENT_ID`) REFERENCES `CLIENT` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SCOPE_MAPPING`
--

LOCK TABLES `SCOPE_MAPPING` WRITE;
/*!40000 ALTER TABLE `SCOPE_MAPPING` DISABLE KEYS */;
INSERT INTO `SCOPE_MAPPING` VALUES ('5060e61b-233b-4347-94e2-4d84d3e67dcc','248a3f39-6dfe-422f-8c29-70c6669842fc'),('e9783fd8-bd55-44f6-bbea-0325f9ca5e03','9fe0f5ad-7ef3-4cd5-b216-9fc0e4021bf4');
/*!40000 ALTER TABLE `SCOPE_MAPPING` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SCOPE_POLICY`
--

DROP TABLE IF EXISTS `SCOPE_POLICY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SCOPE_POLICY` (
  `SCOPE_ID` varchar(36) NOT NULL,
  `POLICY_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`SCOPE_ID`,`POLICY_ID`),
  KEY `IDX_SCOPE_POLICY_POLICY` (`POLICY_ID`),
  CONSTRAINT `FK_FRSRASP13XCX4WNKOG82SSRFY` FOREIGN KEY (`POLICY_ID`) REFERENCES `RESOURCE_SERVER_POLICY` (`ID`),
  CONSTRAINT `FK_FRSRPASS3XCX4WNKOG82SSRFY` FOREIGN KEY (`SCOPE_ID`) REFERENCES `RESOURCE_SERVER_SCOPE` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SCOPE_POLICY`
--

LOCK TABLES `SCOPE_POLICY` WRITE;
/*!40000 ALTER TABLE `SCOPE_POLICY` DISABLE KEYS */;
/*!40000 ALTER TABLE `SCOPE_POLICY` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USERNAME_LOGIN_FAILURE`
--

DROP TABLE IF EXISTS `USERNAME_LOGIN_FAILURE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USERNAME_LOGIN_FAILURE` (
  `REALM_ID` varchar(36) NOT NULL,
  `USERNAME` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `FAILED_LOGIN_NOT_BEFORE` int DEFAULT NULL,
  `LAST_FAILURE` bigint DEFAULT NULL,
  `LAST_IP_FAILURE` varchar(255) DEFAULT NULL,
  `NUM_FAILURES` int DEFAULT NULL,
  PRIMARY KEY (`REALM_ID`,`USERNAME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USERNAME_LOGIN_FAILURE`
--

LOCK TABLES `USERNAME_LOGIN_FAILURE` WRITE;
/*!40000 ALTER TABLE `USERNAME_LOGIN_FAILURE` DISABLE KEYS */;
/*!40000 ALTER TABLE `USERNAME_LOGIN_FAILURE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_ATTRIBUTE`
--

DROP TABLE IF EXISTS `USER_ATTRIBUTE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_ATTRIBUTE` (
  `NAME` varchar(255) NOT NULL,
  `VALUE` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `USER_ID` varchar(36) NOT NULL,
  `ID` varchar(36) NOT NULL DEFAULT 'sybase-needs-something-here',
  PRIMARY KEY (`ID`),
  KEY `IDX_USER_ATTRIBUTE` (`USER_ID`),
  CONSTRAINT `FK_5HRM2VLF9QL5FU043KQEPOVBR` FOREIGN KEY (`USER_ID`) REFERENCES `USER_ENTITY` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_ATTRIBUTE`
--

LOCK TABLES `USER_ATTRIBUTE` WRITE;
/*!40000 ALTER TABLE `USER_ATTRIBUTE` DISABLE KEYS */;
/*!40000 ALTER TABLE `USER_ATTRIBUTE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_CONSENT`
--

DROP TABLE IF EXISTS `USER_CONSENT`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_CONSENT` (
  `ID` varchar(36) NOT NULL,
  `CLIENT_ID` varchar(255) DEFAULT NULL,
  `USER_ID` varchar(36) NOT NULL,
  `CREATED_DATE` bigint DEFAULT NULL,
  `LAST_UPDATED_DATE` bigint DEFAULT NULL,
  `CLIENT_STORAGE_PROVIDER` varchar(36) DEFAULT NULL,
  `EXTERNAL_CLIENT_ID` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `UK_JKUWUVD56ONTGSUHOGM8UEWRT` (`CLIENT_ID`,`CLIENT_STORAGE_PROVIDER`,`EXTERNAL_CLIENT_ID`,`USER_ID`),
  KEY `IDX_USER_CONSENT` (`USER_ID`),
  CONSTRAINT `FK_GRNTCSNT_USER` FOREIGN KEY (`USER_ID`) REFERENCES `USER_ENTITY` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_CONSENT`
--

LOCK TABLES `USER_CONSENT` WRITE;
/*!40000 ALTER TABLE `USER_CONSENT` DISABLE KEYS */;
/*!40000 ALTER TABLE `USER_CONSENT` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_CONSENT_CLIENT_SCOPE`
--

DROP TABLE IF EXISTS `USER_CONSENT_CLIENT_SCOPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_CONSENT_CLIENT_SCOPE` (
  `USER_CONSENT_ID` varchar(36) NOT NULL,
  `SCOPE_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`USER_CONSENT_ID`,`SCOPE_ID`),
  KEY `IDX_USCONSENT_CLSCOPE` (`USER_CONSENT_ID`),
  CONSTRAINT `FK_GRNTCSNT_CLSC_USC` FOREIGN KEY (`USER_CONSENT_ID`) REFERENCES `USER_CONSENT` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_CONSENT_CLIENT_SCOPE`
--

LOCK TABLES `USER_CONSENT_CLIENT_SCOPE` WRITE;
/*!40000 ALTER TABLE `USER_CONSENT_CLIENT_SCOPE` DISABLE KEYS */;
/*!40000 ALTER TABLE `USER_CONSENT_CLIENT_SCOPE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_ENTITY`
--

DROP TABLE IF EXISTS `USER_ENTITY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_ENTITY` (
  `ID` varchar(36) NOT NULL,
  `EMAIL` varchar(255) DEFAULT NULL,
  `EMAIL_CONSTRAINT` varchar(255) DEFAULT NULL,
  `EMAIL_VERIFIED` bit(1) NOT NULL DEFAULT b'0',
  `ENABLED` bit(1) NOT NULL DEFAULT b'0',
  `FEDERATION_LINK` varchar(255) DEFAULT NULL,
  `FIRST_NAME` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `LAST_NAME` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `REALM_ID` varchar(255) DEFAULT NULL,
  `USERNAME` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `CREATED_TIMESTAMP` bigint DEFAULT NULL,
  `SERVICE_ACCOUNT_CLIENT_LINK` varchar(255) DEFAULT NULL,
  `NOT_BEFORE` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`),
  UNIQUE KEY `UK_DYKN684SL8UP1CRFEI6ECKHD7` (`REALM_ID`,`EMAIL_CONSTRAINT`),
  UNIQUE KEY `UK_RU8TT6T700S9V50BU18WS5HA6` (`REALM_ID`,`USERNAME`),
  KEY `IDX_USER_EMAIL` (`EMAIL`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_ENTITY`
--

LOCK TABLES `USER_ENTITY` WRITE;
/*!40000 ALTER TABLE `USER_ENTITY` DISABLE KEYS */;
INSERT INTO `USER_ENTITY` VALUES ('6bd12400-6fc4-402c-9180-83bddbc30526','harry.potter@example.com','harry.potter@example.com',_binary '\0',_binary '',NULL,'Harry','Potter','WESkit','test',1614173019525,NULL,0),('8f5ad792-5fbd-4c9d-b956-86513b92b971',NULL,'35b0667d-ad96-4dd0-98b8-4a5fd9ddd13f',_binary '\0',_binary '',NULL,'otp','otp','WESkit','otp',1614940004264,NULL,0),('b00fd985-a834-4863-9106-11aec150eecd','test.user@example.com','test.user@example.com',_binary '\0',_binary '',NULL,'test','User','WESkit','testuser',1614172452428,NULL,0),('dba63a01-c02a-4fdc-96ee-17c88a1023e3',NULL,'9232914b-f517-4b80-a8ca-5f1f9e294349',_binary '\0',_binary '',NULL,NULL,NULL,'master','admin',1614172212024,NULL,0);
/*!40000 ALTER TABLE `USER_ENTITY` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_FEDERATION_CONFIG`
--

DROP TABLE IF EXISTS `USER_FEDERATION_CONFIG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_FEDERATION_CONFIG` (
  `USER_FEDERATION_PROVIDER_ID` varchar(36) NOT NULL,
  `VALUE` varchar(255) DEFAULT NULL,
  `NAME` varchar(255) NOT NULL,
  PRIMARY KEY (`USER_FEDERATION_PROVIDER_ID`,`NAME`),
  CONSTRAINT `FK_T13HPU1J94R2EBPEKR39X5EU5` FOREIGN KEY (`USER_FEDERATION_PROVIDER_ID`) REFERENCES `USER_FEDERATION_PROVIDER` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_FEDERATION_CONFIG`
--

LOCK TABLES `USER_FEDERATION_CONFIG` WRITE;
/*!40000 ALTER TABLE `USER_FEDERATION_CONFIG` DISABLE KEYS */;
/*!40000 ALTER TABLE `USER_FEDERATION_CONFIG` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_FEDERATION_MAPPER`
--

DROP TABLE IF EXISTS `USER_FEDERATION_MAPPER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_FEDERATION_MAPPER` (
  `ID` varchar(36) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `FEDERATION_PROVIDER_ID` varchar(36) NOT NULL,
  `FEDERATION_MAPPER_TYPE` varchar(255) NOT NULL,
  `REALM_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_USR_FED_MAP_FED_PRV` (`FEDERATION_PROVIDER_ID`),
  KEY `IDX_USR_FED_MAP_REALM` (`REALM_ID`),
  CONSTRAINT `FK_FEDMAPPERPM_FEDPRV` FOREIGN KEY (`FEDERATION_PROVIDER_ID`) REFERENCES `USER_FEDERATION_PROVIDER` (`ID`),
  CONSTRAINT `FK_FEDMAPPERPM_REALM` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_FEDERATION_MAPPER`
--

LOCK TABLES `USER_FEDERATION_MAPPER` WRITE;
/*!40000 ALTER TABLE `USER_FEDERATION_MAPPER` DISABLE KEYS */;
/*!40000 ALTER TABLE `USER_FEDERATION_MAPPER` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_FEDERATION_MAPPER_CONFIG`
--

DROP TABLE IF EXISTS `USER_FEDERATION_MAPPER_CONFIG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_FEDERATION_MAPPER_CONFIG` (
  `USER_FEDERATION_MAPPER_ID` varchar(36) NOT NULL,
  `VALUE` varchar(255) DEFAULT NULL,
  `NAME` varchar(255) NOT NULL,
  PRIMARY KEY (`USER_FEDERATION_MAPPER_ID`,`NAME`),
  CONSTRAINT `FK_FEDMAPPER_CFG` FOREIGN KEY (`USER_FEDERATION_MAPPER_ID`) REFERENCES `USER_FEDERATION_MAPPER` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_FEDERATION_MAPPER_CONFIG`
--

LOCK TABLES `USER_FEDERATION_MAPPER_CONFIG` WRITE;
/*!40000 ALTER TABLE `USER_FEDERATION_MAPPER_CONFIG` DISABLE KEYS */;
/*!40000 ALTER TABLE `USER_FEDERATION_MAPPER_CONFIG` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_FEDERATION_PROVIDER`
--

DROP TABLE IF EXISTS `USER_FEDERATION_PROVIDER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_FEDERATION_PROVIDER` (
  `ID` varchar(36) NOT NULL,
  `CHANGED_SYNC_PERIOD` int DEFAULT NULL,
  `DISPLAY_NAME` varchar(255) DEFAULT NULL,
  `FULL_SYNC_PERIOD` int DEFAULT NULL,
  `LAST_SYNC` int DEFAULT NULL,
  `PRIORITY` int DEFAULT NULL,
  `PROVIDER_NAME` varchar(255) DEFAULT NULL,
  `REALM_ID` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `IDX_USR_FED_PRV_REALM` (`REALM_ID`),
  CONSTRAINT `FK_1FJ32F6PTOLW2QY60CD8N01E8` FOREIGN KEY (`REALM_ID`) REFERENCES `REALM` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_FEDERATION_PROVIDER`
--

LOCK TABLES `USER_FEDERATION_PROVIDER` WRITE;
/*!40000 ALTER TABLE `USER_FEDERATION_PROVIDER` DISABLE KEYS */;
/*!40000 ALTER TABLE `USER_FEDERATION_PROVIDER` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_GROUP_MEMBERSHIP`
--

DROP TABLE IF EXISTS `USER_GROUP_MEMBERSHIP`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_GROUP_MEMBERSHIP` (
  `GROUP_ID` varchar(36) NOT NULL,
  `USER_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`GROUP_ID`,`USER_ID`),
  KEY `IDX_USER_GROUP_MAPPING` (`USER_ID`),
  CONSTRAINT `FK_USER_GROUP_USER` FOREIGN KEY (`USER_ID`) REFERENCES `USER_ENTITY` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_GROUP_MEMBERSHIP`
--

LOCK TABLES `USER_GROUP_MEMBERSHIP` WRITE;
/*!40000 ALTER TABLE `USER_GROUP_MEMBERSHIP` DISABLE KEYS */;
/*!40000 ALTER TABLE `USER_GROUP_MEMBERSHIP` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_REQUIRED_ACTION`
--

DROP TABLE IF EXISTS `USER_REQUIRED_ACTION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_REQUIRED_ACTION` (
  `USER_ID` varchar(36) NOT NULL,
  `REQUIRED_ACTION` varchar(255) NOT NULL DEFAULT ' ',
  PRIMARY KEY (`REQUIRED_ACTION`,`USER_ID`),
  KEY `IDX_USER_REQACTIONS` (`USER_ID`),
  CONSTRAINT `FK_6QJ3W1JW9CVAFHE19BWSIUVMD` FOREIGN KEY (`USER_ID`) REFERENCES `USER_ENTITY` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_REQUIRED_ACTION`
--

LOCK TABLES `USER_REQUIRED_ACTION` WRITE;
/*!40000 ALTER TABLE `USER_REQUIRED_ACTION` DISABLE KEYS */;
/*!40000 ALTER TABLE `USER_REQUIRED_ACTION` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_ROLE_MAPPING`
--

DROP TABLE IF EXISTS `USER_ROLE_MAPPING`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_ROLE_MAPPING` (
  `ROLE_ID` varchar(255) NOT NULL,
  `USER_ID` varchar(36) NOT NULL,
  PRIMARY KEY (`ROLE_ID`,`USER_ID`),
  KEY `IDX_USER_ROLE_MAPPING` (`USER_ID`),
  CONSTRAINT `FK_C4FQV34P1MBYLLOXANG7B1Q3L` FOREIGN KEY (`USER_ID`) REFERENCES `USER_ENTITY` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_ROLE_MAPPING`
--

LOCK TABLES `USER_ROLE_MAPPING` WRITE;
/*!40000 ALTER TABLE `USER_ROLE_MAPPING` DISABLE KEYS */;
INSERT INTO `USER_ROLE_MAPPING` VALUES ('4d51c469-5b72-41ad-b987-b414839904aa','6bd12400-6fc4-402c-9180-83bddbc30526'),('52a3415d-65a9-4314-8805-c85ca05b55d6','6bd12400-6fc4-402c-9180-83bddbc30526'),('9fe0f5ad-7ef3-4cd5-b216-9fc0e4021bf4','6bd12400-6fc4-402c-9180-83bddbc30526'),('e963003d-a6f9-40e1-a14d-df4af02da9be','6bd12400-6fc4-402c-9180-83bddbc30526'),('4d51c469-5b72-41ad-b987-b414839904aa','8f5ad792-5fbd-4c9d-b956-86513b92b971'),('52a3415d-65a9-4314-8805-c85ca05b55d6','8f5ad792-5fbd-4c9d-b956-86513b92b971'),('9fe0f5ad-7ef3-4cd5-b216-9fc0e4021bf4','8f5ad792-5fbd-4c9d-b956-86513b92b971'),('e963003d-a6f9-40e1-a14d-df4af02da9be','8f5ad792-5fbd-4c9d-b956-86513b92b971'),('4d51c469-5b72-41ad-b987-b414839904aa','b00fd985-a834-4863-9106-11aec150eecd'),('526de35b-4b08-492e-9f53-2a15aaf836b3','b00fd985-a834-4863-9106-11aec150eecd'),('52a3415d-65a9-4314-8805-c85ca05b55d6','b00fd985-a834-4863-9106-11aec150eecd'),('9fe0f5ad-7ef3-4cd5-b216-9fc0e4021bf4','b00fd985-a834-4863-9106-11aec150eecd'),('e963003d-a6f9-40e1-a14d-df4af02da9be','b00fd985-a834-4863-9106-11aec150eecd'),('02a5d5df-98a6-4b2d-8bbe-bde39eec7995','dba63a01-c02a-4fdc-96ee-17c88a1023e3'),('248a3f39-6dfe-422f-8c29-70c6669842fc','dba63a01-c02a-4fdc-96ee-17c88a1023e3'),('9c8169aa-b379-409b-bbe3-42592be27747','dba63a01-c02a-4fdc-96ee-17c88a1023e3'),('b0025059-e023-4fde-836c-a0e12b9941b6','dba63a01-c02a-4fdc-96ee-17c88a1023e3'),('cbc5dbe2-ac59-4b57-a641-387d94e759c6','dba63a01-c02a-4fdc-96ee-17c88a1023e3');
/*!40000 ALTER TABLE `USER_ROLE_MAPPING` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_SESSION`
--

DROP TABLE IF EXISTS `USER_SESSION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_SESSION` (
  `ID` varchar(36) NOT NULL,
  `AUTH_METHOD` varchar(255) DEFAULT NULL,
  `IP_ADDRESS` varchar(255) DEFAULT NULL,
  `LAST_SESSION_REFRESH` int DEFAULT NULL,
  `LOGIN_USERNAME` varchar(255) DEFAULT NULL,
  `REALM_ID` varchar(255) DEFAULT NULL,
  `REMEMBER_ME` bit(1) NOT NULL DEFAULT b'0',
  `STARTED` int DEFAULT NULL,
  `USER_ID` varchar(255) DEFAULT NULL,
  `USER_SESSION_STATE` int DEFAULT NULL,
  `BROKER_SESSION_ID` varchar(255) DEFAULT NULL,
  `BROKER_USER_ID` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_SESSION`
--

LOCK TABLES `USER_SESSION` WRITE;
/*!40000 ALTER TABLE `USER_SESSION` DISABLE KEYS */;
/*!40000 ALTER TABLE `USER_SESSION` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `USER_SESSION_NOTE`
--

DROP TABLE IF EXISTS `USER_SESSION_NOTE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USER_SESSION_NOTE` (
  `USER_SESSION` varchar(36) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `VALUE` text,
  PRIMARY KEY (`USER_SESSION`,`NAME`),
  CONSTRAINT `FK5EDFB00FF51D3472` FOREIGN KEY (`USER_SESSION`) REFERENCES `USER_SESSION` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `USER_SESSION_NOTE`
--

LOCK TABLES `USER_SESSION_NOTE` WRITE;
/*!40000 ALTER TABLE `USER_SESSION_NOTE` DISABLE KEYS */;
/*!40000 ALTER TABLE `USER_SESSION_NOTE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `WEB_ORIGINS`
--

DROP TABLE IF EXISTS `WEB_ORIGINS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `WEB_ORIGINS` (
  `CLIENT_ID` varchar(36) NOT NULL,
  `VALUE` varchar(255) NOT NULL,
  PRIMARY KEY (`CLIENT_ID`,`VALUE`),
  KEY `IDX_WEB_ORIG_CLIENT` (`CLIENT_ID`),
  CONSTRAINT `FK_LOJPHO213XCX4WNKOG82SSRFY` FOREIGN KEY (`CLIENT_ID`) REFERENCES `CLIENT` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `WEB_ORIGINS`
--

LOCK TABLES `WEB_ORIGINS` WRITE;
/*!40000 ALTER TABLE `WEB_ORIGINS` DISABLE KEYS */;
INSERT INTO `WEB_ORIGINS` VALUES ('4f8082eb-2eb8-4217-9b7d-e70fa5da2c6a','+'),('6445f320-dddf-4a4f-8e54-4ec19fbcb7ae','+');
/*!40000 ALTER TABLE `WEB_ORIGINS` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-03-29  8:13:49
