class Quotation {
  final int? id;
  final String piName;
  final String products;
  final double totalAmount;
  final String status;
  final String? createdAt;

  const Quotation({
    this.id,
    required this.piName,
    this.products = '[]',
    this.totalAmount = 0,
    this.status = 'draft',
    this.createdAt,
  });

  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'pi_name': piName,
      'products': products,
      'total_amount': totalAmount,
      'status': status,
    };
  }

  factory Quotation.fromMap(Map<String, dynamic> map) {
    return Quotation(
      id: map['id'] as int?,
      piName: map['pi_name'] as String,
      products: map['products'] as String? ?? '[]',
      totalAmount: (map['total_amount'] as num?)?.toDouble() ?? 0,
      status: map['status'] as String? ?? 'draft',
      createdAt: map['created_at'] as String?,
    );
  }

  Quotation copyWith({
    int? id,
    String? piName,
    String? products,
    double? totalAmount,
    String? status,
    String? createdAt,
  }) {
    return Quotation(
      id: id ?? this.id,
      piName: piName ?? this.piName,
      products: products ?? this.products,
      totalAmount: totalAmount ?? this.totalAmount,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
