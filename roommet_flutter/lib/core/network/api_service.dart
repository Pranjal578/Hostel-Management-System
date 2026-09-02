import 'package:dio/dio.dart';
import 'package:roommet_flutter/core/config/app_config.dart';
import 'package:roommet_flutter/core/storage/token_storage.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;

  late final Dio _dio;

  ApiService._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConfig.baseUrl,
      connectTimeout: AppConfig.connectTimeout,
      receiveTimeout: AppConfig.receiveTimeout,
      headers: {'Content-Type': 'application/json'},
    ));

    // JWT interceptor: attach token to every request
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await TokenStorage.getToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) {
        handler.next(error);
      },
    ));
  }

  Dio get client => _dio;

  // ── Auth ──────────────────────────────────────────────────────

  Future<Map<String, dynamic>> login(String email, String password) async {
    final res = await _dio.post('/auth/login', data: {'email': email, 'password': password});
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> verifyOtp(String email, String otp) async {
    final res = await _dio.post('/auth/verify-otp', data: {'email': email, 'otp_code': otp});
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> loginWithGoogle({String? idToken, String? accessToken}) async {
    final res = await _dio.post('/auth/google', data: {
      if (idToken != null) 'id_token': idToken,
      if (accessToken != null) 'access_token': accessToken,
    });
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getMe() async {
    final res = await _dio.get('/auth/me');
    return res.data as Map<String, dynamic>;
  }

  // ── Resident ──────────────────────────────────────────────────

  Future<Map<String, dynamic>> getResidentProfile() async {
    final res = await _dio.get('/resident/profile');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getResidentQr() async {
    final res = await _dio.get('/resident/qr');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getResidentPayments({int page = 1}) async {
    final res = await _dio.get('/resident/payments', queryParameters: {'page': page});
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> submitPayment({
    required double amount,
    required String transactionId,
    required String paymentDate,
    required String filePath,
    required String fileName,
  }) async {
    final formData = FormData.fromMap({
      'amount': amount.toString(),
      'transaction_id': transactionId,
      'payment_date': paymentDate,
      'receipt': await MultipartFile.fromFile(filePath, filename: fileName),
    });
    final res = await _dio.post('/resident/payments',
        data: formData,
        options: Options(contentType: 'multipart/form-data'));
    return res.data as Map<String, dynamic>;
  }

  Future<List<dynamic>> getResidentNotices() async {
    final res = await _dio.get('/resident/notices');
    return res.data as List<dynamic>;
  }

  // ── Owner ─────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getOwnerDashboard() async {
    final res = await _dio.get('/owner/dashboard');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getOwnerResidents({
    int page = 1,
    String? search,
    String? status,
    int? hostelId,
  }) async {
    final res = await _dio.get('/owner/residents', queryParameters: {
      'page': page,
      if (search != null && search.isNotEmpty) 'q': search,
      if (status != null && status.isNotEmpty) 'status': status,
      if (hostelId != null) 'hostel_id': hostelId,
    });
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> approveResident(int residentId, {String? roomNumber}) async {
    final res = await _dio.post('/owner/residents/$residentId/approve',
        data: {'room_number': roomNumber ?? ''});
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> rejectResident(int residentId) async {
    final res = await _dio.post('/owner/residents/$residentId/reject');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getOwnerPayments({int page = 1, String status = 'Pending'}) async {
    final res = await _dio.get('/owner/payments', queryParameters: {'page': page, 'status': status});
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> verifyPayment(int paymentId, String action, {String? reason}) async {
    final res = await _dio.post('/owner/payments/$paymentId/verify',
        data: {'action': action, 'reason': reason ?? ''});
    return res.data as Map<String, dynamic>;
  }

  Future<List<dynamic>> getOwnerNotices({int? hostelId}) async {
    final res = await _dio.get('/owner/notices',
        queryParameters: hostelId != null ? {'hostel_id': hostelId} : {});
    return res.data as List<dynamic>;
  }

  Future<Map<String, dynamic>> postNotice(int hostelId, String title, String message) async {
    final res = await _dio.post('/owner/notices',
        data: {'hostel_id': hostelId, 'title': title, 'message': message});
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getResidentDetail(int residentId) async {
    final res = await _dio.get('/owner/resident/$residentId');
    return res.data as Map<String, dynamic>;
  }

  // ── Chat ──────────────────────────────────────────────────────

  Future<List<dynamic>> getChatMessages(int recipientId) async {
    final res = await _dio.get('/chat/$recipientId');
    return res.data as List<dynamic>;
  }

  Future<Map<String, dynamic>> sendMessage(int recipientId, String content) async {
    final res = await _dio.post('/chat/$recipientId',
        data: {'message_content': content});
    return res.data as Map<String, dynamic>;
  }

  Future<List<dynamic>> getChatContacts() async {
    final res = await _dio.get('/chat/contacts');
    return res.data as List<dynamic>;
  }

  // ── Pharmacy ──────────────────────────────────────────────────

  Future<Map<String, dynamic>> getMedicines({int page = 1, String? search, String? category}) async {
    final res = await _dio.get('/pharmacy/medicines', queryParameters: {
      'page': page,
      if (search != null && search.isNotEmpty) 'q': search,
      if (category != null && category.isNotEmpty) 'category': category,
    });
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getMedicineDetail(int id) async {
    final res = await _dio.get('/pharmacy/medicines/$id');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> placeOrder(Map<String, dynamic> orderData) async {
    final res = await _dio.post('/pharmacy/orders', data: orderData);
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getMyOrders({int page = 1}) async {
    final res = await _dio.get('/pharmacy/orders/my', queryParameters: {'page': page});
    return res.data as Map<String, dynamic>;
  }

  // ── Admin ─────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getAdminStats() async {
    final res = await _dio.get('/admin/stats');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getAdminResidents({int page = 1, String? search}) async {
    final res = await _dio.get('/admin/residents', queryParameters: {
      'page': page,
      if (search != null && search.isNotEmpty) 'q': search,
    });
    return res.data as Map<String, dynamic>;
  }

  Future<List<dynamic>> getAdminOwners() async {
    final res = await _dio.get('/admin/owners');
    return res.data as List<dynamic>;
  }

  Future<List<dynamic>> getAdminShops() async {
    final res = await _dio.get('/admin/shops');
    return res.data as List<dynamic>;
  }

  Future<Map<String, dynamic>> verifyShop(int shopId, String action) async {
    final res = await _dio.post('/admin/shops/$shopId/verify', data: {'action': action});
    return res.data as Map<String, dynamic>;
  }

  // ── Shop Owner ────────────────────────────────────────────────

  Future<Map<String, dynamic>> getShopDashboard() async {
    final res = await _dio.get('/shop/dashboard');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getShopOrders({int page = 1, String? status}) async {
    final res = await _dio.get('/shop/orders', queryParameters: {
      'page': page,
      if (status != null && status.isNotEmpty) 'status': status,
    });
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateOrderStatus(int orderId, String action, {String? reason}) async {
    final res = await _dio.post('/shop/orders/$orderId/status',
        data: {'action': action, if (reason != null) 'reason': reason});
    return res.data as Map<String, dynamic>;
  }

  Future<List<dynamic>> getShopInventory() async {
    final res = await _dio.get('/shop/inventory');
    return res.data as List<dynamic>;
  }

  // ── Public ────────────────────────────────────────────────────

  Future<List<dynamic>> getPublicHostels({String? search}) async {
    final res = await _dio.get('/hostels/public',
        queryParameters: search != null ? {'q': search} : {});
    return res.data as List<dynamic>;
  }
}
