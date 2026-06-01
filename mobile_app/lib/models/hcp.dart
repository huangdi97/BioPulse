import 'dart:convert';

class HCP {
  final int? id;
  final String name;
  final String hospital;
  final String? department;
  final String? title;
  final String? phone;
  final String? email;
  final bool isActive;
  final List<String> tags;
  final String? lastVisitDate;
  final String createdAt;

  const HCP({
    this.id,
    required this.name,
    required this.hospital,
    this.department,
    this.title,
    this.phone,
    this.email,
    this.isActive = true,
    this.tags = const [],
    this.lastVisitDate,
    required this.createdAt,
  });

  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'name': name,
      'hospital': hospital,
      'department': department,
      'title': title,
      'phone': phone,
      'email': email,
      'is_active': isActive ? 1 : 0,
      'tags': jsonEncode(tags),
      'last_visit_date': lastVisitDate,
      'created_at': createdAt,
    };
  }

  factory HCP.fromMap(Map<String, dynamic> map) {
    return HCP(
      id: map['id'] as int?,
      name: map['name'] as String,
      hospital: map['hospital'] as String,
      department: map['department'] as String?,
      title: map['title'] as String?,
      phone: map['phone'] as String?,
      email: map['email'] as String?,
      isActive: (map['is_active'] as int?) == 1,
      tags: map['tags'] != null
          ? List<String>.from(jsonDecode(map['tags'] as String))
          : const [],
      lastVisitDate: map['last_visit_date'] as String?,
      createdAt: map['created_at'] as String,
    );
  }

  HCP copyWith({
    int? id,
    String? name,
    String? hospital,
    String? department,
    String? title,
    String? phone,
    String? email,
    bool? isActive,
    List<String>? tags,
    String? lastVisitDate,
    String? createdAt,
  }) {
    return HCP(
      id: id ?? this.id,
      name: name ?? this.name,
      hospital: hospital ?? this.hospital,
      department: department ?? this.department,
      title: title ?? this.title,
      phone: phone ?? this.phone,
      email: email ?? this.email,
      isActive: isActive ?? this.isActive,
      tags: tags ?? this.tags,
      lastVisitDate: lastVisitDate ?? this.lastVisitDate,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
